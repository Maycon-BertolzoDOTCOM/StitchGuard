"""Worker ARQ — processa jobs de forma assincrona via Redis.

Suporta:
- processar_pedido: pipeline individual (L3 -> L4 -> otimização)
- processar_batch: processamento em lote de múltiplos arquivos
"""
import json
import os
import tempfile
from datetime import datetime, timezone

import structlog
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from arq.worker import Retry

from infra.storage import SessionLocal, Job, Validacao

log = structlog.get_logger()

STATUS_PENDENTE = "pendente"
STATUS_PROCESSANDO = "processando"
STATUS_CONCLUIDO = "concluido"
STATUS_ERRO = "erro"


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


async def processar_pedido(ctx: dict, job_id: str, payload_json: str) -> dict:
    """Executa o pipeline L3->L4 no worker, separado da API."""
    log.info("worker.inicio", job_id=job_id)
    redis: ArqRedis = ctx["redis_pool"]

    # Atualizar status para processando
    await _atualizar_status_redis(redis, job_id, STATUS_PROCESSANDO)

    try:
        from pydantic import BaseModel

        class PedidoPayload(BaseModel):
            arte: str | None = None
            tecido: str | None = None
            preset: str | None = None
            compensacao: str | None = None
            underlay: bool | None = None
            maquina: str | None = None
            dificuldade: str = "auto"

        payload = PedidoPayload.model_validate_json(payload_json)

        # Pipeline L3 -> L4 -> otimizacao
        from application.main import _pipeline
        resultado = _pipeline(payload)

        await _atualizar_status_redis(redis, job_id, STATUS_CONCLUIDO, resultado=resultado)

        # Persistir validacoes no Postgres
        if "itens" in resultado:
            _salvar_validacoes_postgres(job_id, resultado["itens"])

        log.info("worker.concluido", job_id=job_id, pontos=resultado["resumo"]["pontos"])
        return resultado

    except Exception as exc:
        await _atualizar_status_redis(redis, job_id, STATUS_ERRO, erro=str(exc))
        log.error("worker.erro", job_id=job_id, erro=str(exc))
        raise Retry(defer=ctx["job_try"] * 10)


async def processar_batch(ctx: dict, batch_id: str, arquivos_json: str, tecido: str, formato: str) -> dict:
    """Processa batch de múltiplos arquivos de forma assíncrona.

    Args:
        batch_id: ID do batch
        arquivos_json: JSON array com [{filename, path}]
        tecido: Tipo de tecido
        formato: Formato de saída
    """
    log.info("worker.batch.inicio", batch_id=batch_id, n_arquivos=len(arquivos_json))
    redis: ArqRedis = ctx["redis_pool"]

    await _atualizar_status_redis(redis, batch_id, STATUS_PROCESSANDO)

    try:
        import pyembroidery as pe
        from generation.inkstitch_provider import auto_digitize

        arquivos = json.loads(arquivos_json)
        resultados = []
        erros = []
        total_pontos = 0

        for i, arq in enumerate(arquivos):
            filename = arq.get("filename", f"arq_{i}")
            path = arq.get("path")

            try:
                if not path or not os.path.exists(path):
                    erros.append({"filename": filename, "erro": "Arquivo não encontrado"})
                    continue

                ext = os.path.splitext(filename)[1].lower()

                if ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
                    pontos = auto_digitize(path, tecido=tecido)
                    if not pontos:
                        erros.append({"filename": filename, "erro": "Nenhum ponto gerado"})
                        continue

                    pattern = pe.EmbPattern()
                    for p in pontos:
                        tipo = p.get("type", "STITCH")
                        if tipo == "JUMP":
                            pattern.add_stitch_absolute(pe.JUMP, p["x"], p["y"])
                        elif tipo == "TRIM":
                            pattern.add_stitch_absolute(pe.TRIM, p["x"], p["y"])
                        else:
                            pattern.add_stitch_absolute(pe.STITCH, p["x"], p["y"])
                    pattern.add_command(pe.END)

                    dst_path = os.path.join(tempfile.gettempdir(), f"{batch_id}_{i}.{formato}")
                    pe.write(pattern, dst_path)

                    n_stitches = len(pattern.stitches)
                    total_pontos += n_stitches
                    resultados.append({
                        "filename": filename,
                        "dst": dst_path,
                        "pontos": n_stitches,
                        "status": "convertido",
                    })
                else:
                    erros.append({"filename": filename, "erro": f"Formato {ext} não suportado"})

            except Exception as e:
                erros.append({"filename": filename, "erro": str(e)})
                log.error("worker.batch.erro_item", filename=filename, erro=str(e))

        resultado = {
            "batch_id": batch_id,
            "total": len(arquivos),
            "processados": len(resultados),
            "erros": len(erros),
            "resultados": resultados,
            "detalhes_erros": erros,
            "total_pontos": total_pontos,
        }

        await _atualizar_status_redis(redis, batch_id, STATUS_CONCLUIDO, resultado=resultado)
        log.info("worker.batch.concluido", batch_id=batch_id, processados=len(resultados))
        return resultado

    except Exception as exc:
        await _atualizar_status_redis(redis, batch_id, STATUS_ERRO, erro=str(exc))
        log.error("worker.batch.erro", batch_id=batch_id, erro=str(exc))
        raise Retry(defer=ctx["job_try"] * 5)


async def _atualizar_status_redis(
    redis: ArqRedis, job_id: str, status: str,
    resultado: dict | None = None, erro: str | None = None,
) -> None:
    data = {
        "job_id": job_id,
        "status": status,
        "atualizado_em": _agora(),
    }
    if resultado is not None:
        data["resultado"] = json.dumps(resultado, ensure_ascii=False)
    if erro is not None:
        data["erro"] = erro
    await redis.hset(f"job:{job_id}", mapping=data)
    await redis.expire(f"job:{job_id}", 86400)


async def obter_job_redis(redis: ArqRedis, job_id: str) -> dict | None:
    data = await redis.hgetall(f"job:{job_id}")
    if not data:
        return None
    return {
        "job_id": data.get(b"job_id", b"").decode(),
        "status": data.get(b"status", b"").decode(),
        "resultado": json.loads(data[b"resultado"]) if b"resultado" in data else None,
        "erro": data.get(b"erro", b"").decode() if b"erro" in data else None,
        "atualizado_em": data.get(b"atualizado_em", b"").decode(),
    }


def _salvar_validacoes_postgres(job_id: str, itens: dict) -> None:
    agora = _agora()
    with SessionLocal() as session:
        for nome, item in itens.items():
            session.add(Validacao(
                job_id=job_id,
                item=nome,
                score=item.get("score"),
                aprovado=item.get("aprovado", False),
                detalhe=item.get("detalhe"),
                criado_em=agora,
            ))
        session.commit()


class WorkerSettings:
    functions = [processar_pedido, processar_batch]
    redis_settings = RedisSettings.from_dsn(
        os.environ.get("REDIS_URL", "redis://localhost:6379")
    )
    max_tries = 3
    job_timeout = 300
    keep_result = 3600

    async def on_startup(ctx: dict) -> None:
        ctx["redis_pool"] = await create_pool(
            RedisSettings.from_dsn(
                os.environ.get("REDIS_URL", "redis://localhost:6379")
            )
        )

    async def on_shutdown(ctx: dict) -> None:
        await ctx["redis_pool"].close()
