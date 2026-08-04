"""L1 — Application: API FastAPI para o pipeline StitchGuard.

Endpoints:
- GET  /health                         -> health check
- GET  /v1/maquinas                    -> catalogo de maquinas
- GET  /v1/presets                     -> presets de tecido
- POST /v1/validar                     -> valida um .dst (multipart + form)
- POST /v1/pedido                      -> cria job gerar->validar->otimizar (202 + jobId)
- GET  /v1/pedido/{job_id}/status      -> polling de status do job (fila persistente)
- GET  /v1/pedido/{job_id}/validacoes  -> 11 itens do checklist
- POST /v1/pedido/{job_id}/editar      -> pos-edicao avancada (7 operacoes)
- GET  /v1/pedido/{job_id}/laudo       -> gera laudo tecnico HTML
- GET  /v1/pedido/{job_id}/laudo/html  -> retorna HTML do laudo diretamente
- GET  /v1/artefatos/{job_id}          -> download do .dst gerado
- POST /v1/auth/register               -> registro de usuario
- POST /v1/auth/login                  -> login JWT
- POST /v1/billing/webhook             -> Asaas (stub, depende de credencial)
"""
import json
import os
import shutil
import tempfile
import threading
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

from domain.maquinas import MAQUINAS, listar_maquinas
from domain.presets import TECIDOS
from generation.router import route
from infra import fila
from validation.checklist import run_checklist
from validation.metrics import StitchMetrics

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia lifecycle da aplicacao (Redis pool para ARQ)."""
    # Startup: tentar conectar Redis (opcional, fallback para SQLite)
    redis_url = os.environ.get("REDIS_URL")
    app.state.arq_pool = None
    if redis_url:
        try:
            from arq import create_pool
            from arq.connections import RedisSettings
            app.state.arq_pool = await create_pool(RedisSettings.from_dsn(redis_url))
            log.info("redis.conectado", url=redis_url)
        except Exception as e:
            log.warning("redis.fallback_sqlite", erro=str(e))
    yield
    # Shutdown
    if app.state.arq_pool:
        await app.state.arq_pool.close()


app = FastAPI(
    title="StitchGuard API",
    version="0.2.0",
    description="Fabrica autonoma de matrizes de bordado — gerar, validar e otimizar.",
    lifespan=lifespan,
)

# Incluir router de auth
from application.auth.router import router as auth_router
app.include_router(auth_router)

_ARTEFATOS = tempfile.mkdtemp(prefix="stitchguard-")


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
class PedidoRequest(BaseModel):
    """Corpo de POST /v1/pedido. 'arte' é o JSON da arte como string (None => amostra padrão)."""

    arte: str | None = None
    tecido: str | None = None
    preset: str | None = None
    compensacao: str | None = None
    underlay: bool | None = None
    maquina: str | None = None
    dificuldade: str = "auto"


class EditarOperacao(BaseModel):
    """Uma operação de pós-edição."""

    tipo: str
    valor_mm: float | None = None
    fator: float | None = None
    ordem: list[int] | None = None
    indice: int | None = None
    x: float | None = None
    y: float | None = None
    tipo_underlay: str | None = None
    tolerancia_mm: float | None = None


class EditarRequest(BaseModel):
    """Corpo de POST /v1/pedido/{job_id}/editar."""

    operacoes: list[EditarOperacao]


# ---------------------------------------------------------------------------
# Pipeline (L3 -> L4 -> otimizacao)
# ---------------------------------------------------------------------------
def _params(payload: PedidoRequest) -> dict:
    return {
        "tecido": payload.tecido,
        "preset": payload.preset,
        "compensacao": payload.compensacao,
        "underlay": payload.underlay,
        "maquina_id": payload.maquina,
    }


def _pipeline(payload: PedidoRequest) -> dict:
    """Executa gerar (L3) -> validar (L4) -> otimizar e devolve JSON serializavel."""
    params = _params(payload)
    arte_path = None
    if payload.arte:
        arte_path = os.path.join(_ARTEFATOS, f"{uuid.uuid4().hex[:8]}.json")
        with open(arte_path, "w", encoding="utf-8") as fh:
            fh.write(payload.arte)

    dst = route(arte_path, params, difficulty=payload.dificuldade)
    if not payload.arte:
        dst = _movar_artefato(dst)

    metrics = StitchMetrics(dst)
    resultado = run_checklist(metrics, params)
    return {
        "dst": os.path.basename(dst),
        "params": params,
        "resumo": {
            "pontos": metrics.stitch_count,
            "passo_medio_mm": round(metrics.average_stitch_length_mm(), 2),
            "maior_salto_mm": round(metrics.max_jump_mm(), 2),
            "largura_mm": round(metrics.width_mm, 2),
            "altura_mm": round(metrics.height_mm, 2),
        },
        **resultado,
    }


def _movar_artefato(dst: str) -> str:
    """Move o .dst gerado para o diretorio de artefatos (nome unico)."""
    nome = f"{uuid.uuid4().hex[:8]}.dst"
    destino = os.path.join(_ARTEFATOS, nome)
    shutil.move(dst, destino)
    return destino


def _processar_job(job_id: str, payload: PedidoRequest) -> None:
    """Executa o pipeline e persiste o resultado na fila."""
    log.info("job.inicio", job_id=job_id)
    fila.atualizar_status(job_id, fila.STATUS_PROCESSANDO)
    try:
        resultado = _pipeline(payload)
        fila.atualizar_status(job_id, fila.STATUS_CONCLUIDO, resultado=resultado)
        # Persiste validacoes por item (checklist 11 itens)
        if "itens" in resultado:
            fila.salvar_validacoes(job_id, resultado["itens"])
        log.info("job.concluido", job_id=job_id, pontos=resultado["resumo"]["pontos"])
    except Exception as exc:
        fila.atualizar_status(job_id, fila.STATUS_ERRO, erro=str(exc))
        log.error("job.erro", job_id=job_id, erro=str(exc))


# ---------------------------------------------------------------------------
# Health / catalogo
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "servico": "stitchguard", "versao": app.version}


@app.get("/v1/maquinas")
def maquinas():
    return {"ids": listar_maquinas(), "catalogo": MAQUINAS}


@app.get("/v1/presets")
def presets():
    return {"tecidos": sorted(TECIDOS.keys()), "presets": TECIDOS}


# ---------------------------------------------------------------------------
# Upload de imagem (SVG/PNG) -> conversao automatica para .dst
# ---------------------------------------------------------------------------
@app.post("/v1/upload")
async def upload_imagem(
    arquivo: UploadFile = File(..., description="SVG ou PNG para converter em .dst"),
    tecido: str | None = Form(None),
):
    """Recebe SVG/PNG, extrai silhueta e gera .dst com preview."""
    from generation.image_processor import processar_imagem

    extensoes_validas = (".svg", ".png", ".jpg", ".jpeg", ".bmp", ".gif")
    if not arquivo.filename.lower().endswith(extensoes_validas):
        raise HTTPException(
            status_code=400,
            detail=f"Formato nao suportado. Use: {', '.join(extensoes_validas)}",
        )

    # Salvar arquivo temporario
    ext = os.path.splitext(arquivo.filename)[1]
    caminho_entrada = os.path.join(_ARTEFATOS, f"{uuid.uuid4().hex[:8]}{ext}")
    conteudo = await arquivo.read()
    with open(caminho_entrada, "wb") as fh:
        fh.write(conteudo)

    try:
        pattern = processar_imagem(caminho_entrada, tecido or "generico")

        if not pattern.stitches:
            raise HTTPException(status_code=422, detail="Nao foi possivel extrair pontos da imagem.")

        # Salvar .dst
        dst_nome = f"{uuid.uuid4().hex[:8]}.dst"
        dst_path = os.path.join(_ARTEFATOS, dst_nome)
        import pyembroidery as pe
        pe.write(pattern, dst_path)

        # Gerar preview SVG
        svg_nome = f"{uuid.uuid4().hex[:8]}.svg"
        svg_path = os.path.join(_ARTEFATOS, svg_nome)
        pe.write(pattern, svg_path)

        log.info("upload.concluido", arquivo=arquivo.filename, stitches=len(pattern.stitches))

        return {
            "arquivo_entrada": arquivo.filename,
            "dst": dst_nome,
            "preview_svg": svg_nome,
            "resumo": {
                "stitches": len(pattern.stitches),
                "cores": len(pattern.threadlist),
                "largura_mm": round(pattern.bounds()[2] - pattern.bounds()[0], 2),
                "altura_mm": round(pattern.bounds()[3] - pattern.bounds()[1], 2),
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        if os.path.exists(caminho_entrada):
            os.unlink(caminho_entrada)


# ---------------------------------------------------------------------------
# Validacao (L4) de arquivo enviado
# ---------------------------------------------------------------------------
@app.post("/v1/validar")
async def validar(
    arquivo: UploadFile = File(..., description="Arquivo .dst"),
    tecido: str | None = Form(None),
    preset: str | None = Form(None),
    compensacao: str | None = Form(None),
    underlay: bool | None = Form(None),
    maquina: str | None = Form(None),
):
    if not arquivo.filename.lower().endswith(".dst"):
        raise HTTPException(status_code=400, detail="Somente arquivos .dst.")

    caminho = os.path.join(_ARTEFATOS, f"{uuid.uuid4().hex[:8]}.dst")
    conteudo = await arquivo.read()
    with open(caminho, "wb") as fh:
        fh.write(conteudo)

    params = {
        "tecido": tecido,
        "preset": preset,
        "compensacao": compensacao,
        "underlay": underlay,
        "maquina_id": maquina,
    }
    metrics = StitchMetrics(caminho)
    resultado = run_checklist(metrics, params)
    return {
        "arquivo": arquivo.filename,
        "resumo": {
            "pontos": metrics.stitch_count,
            "passo_medio_mm": round(metrics.average_stitch_length_mm(), 2),
            "maior_salto_mm": round(metrics.max_jump_mm(), 2),
            "largura_mm": round(metrics.width_mm, 2),
            "altura_mm": round(metrics.height_mm, 2),
        },
        **resultado,
    }


# ---------------------------------------------------------------------------
# Pedido (gerar -> validar -> otimizar) com polling persistente + idempotencia
# ---------------------------------------------------------------------------
from typing import Annotated
from fastapi import Depends
from application.auth.dependencies import get_current_user
from infra.storage import User

@app.post("/v1/pedido", status_code=202)
def criar_pedido(
    payload: PedidoRequest,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
):
    params = _params(payload)
    content_hash = fila.calcular_hash(payload.arte, params)

    # Idempotencia: se job identico existe e nao expirou, retorna ele
    existente = fila.obter_por_hash(content_hash)
    if existente is not None:
        response.headers["X-Idempotency"] = "REPLAY"
        log.info("pedido.replay", job_id=existente["job_id"])
        return {"job_id": existente["job_id"], "status": existente["status"]}

    job_id = uuid.uuid4().hex[:12]
    fila.enfileirar(job_id, payload.arte, params, content_hash=content_hash)
    thread = threading.Thread(target=_processar_job, args=(job_id, payload), daemon=True)
    thread.start()
    log.info("pedido.criado", job_id=job_id, tecido=payload.tecido, maquina=payload.maquina)
    return {"job_id": job_id, "status": fila.STATUS_PENDENTE}


@app.get("/v1/pedido/{job_id}/status")
def status_pedido(job_id: str):
    job = fila.obter_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "resultado": job["resultado"],
        "erro": job["erro"],
        "criado_em": job["criado_em"],
        "atualizado_em": job["atualizado_em"],
    }


@app.get("/v1/artefatos/{job_id}")
def baixar_artefato(job_id: str):
    job = fila.obter_job(job_id)
    if job is None or job["status"] != fila.STATUS_CONCLUIDO:
        raise HTTPException(status_code=404, detail="Artefato indisponivel.")
    nome = job["resultado"]["dst"]
    caminho = os.path.join(_ARTEFATOS, nome)
    if not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado.")
    return FileResponse(caminho, media_type="application/octet-stream", filename=nome)


@app.get("/v1/arquivos/{filename}")
def baixar_arquivo(filename: str):
    """Download direto de arquivo gerado (upload)."""
    caminho = os.path.join(_ARTEFATOS, filename)
    if not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado.")
    if filename.lower().endswith(".svg"):
        media_type = "image/svg+xml"
    elif filename.lower().endswith(".dst"):
        media_type = "application/octet-stream"
    else:
        media_type = "application/octet-stream"
    return FileResponse(caminho, media_type=media_type, filename=filename)


def _dst_para_svg(dst_path: str) -> str:
    """Converte .dst para SVG usando pyembroidery nativo."""
    import pyembroidery as pe
    import tempfile
    pattern = pe.read(dst_path)
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w") as tmp:
        tmp_path = tmp.name
    try:
        pe.write(pattern, tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get("/v1/preview/{job_id}")
def preview_svg(job_id: str):
    """Retorna SVG do bordado gerado (preview visual)."""
    job = fila.obter_job(job_id)
    if job is None or job["status"] != fila.STATUS_CONCLUIDO:
        raise HTTPException(status_code=404, detail="Preview indisponivel.")
    nome = job["resultado"]["dst"]
    caminho = os.path.join(_ARTEFATOS, nome)
    if not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="Arquivo .dst nao encontrado.")
    svg = _dst_para_svg(caminho)
    return Response(content=svg, media_type="image/svg+xml")


@app.post("/v1/pedido/{job_id}/editar")
def editar_pedido(job_id: str, payload: EditarRequest):
    """Aplica operações de pós-edição em um job existente.

    Retorna SVG preview, .dst atualizado e re-validação.
    """
    from post_editor.editor import aplicar_operacoes, salvar_pattern
    from validation.checklist import run_checklist
    from validation.metrics import StitchMetrics

    job = fila.obter_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")
    if job["status"] != fila.STATUS_CONCLUIDO:
        raise HTTPException(status_code=400, detail="Job ainda nao concluido.")

    dst_nome = job["resultado"]["dst"]
    dst_caminho = os.path.join(_ARTEFATOS, dst_nome)
    if not os.path.exists(dst_caminho):
        raise HTTPException(status_code=404, detail="Arquivo .dst nao encontrado.")

    # Converter payload para lista de dicts
    operacoes = []
    for op in payload.operacoes:
        operacao = {"tipo": op.tipo}
        if op.valor_mm is not None:
            operacao["valor_mm"] = op.valor_mm
        if op.fator is not None:
            operacao["fator"] = op.fator
        if op.ordem is not None:
            operacao["ordem"] = op.ordem
        if op.indice is not None:
            operacao["indice"] = op.indice
        if op.x is not None:
            operacao["x"] = op.x
        if op.y is not None:
            operacao["y"] = op.y
        if op.tipo_underlay is not None:
            operacao["tipo_underlay"] = op.tipo_underlay
        if op.tolerancia_mm is not None:
            operacao["tolerancia_mm"] = op.tolerancia_mm
        operacoes.append(operacao)

    try:
        resultado = aplicar_operacoes(dst_caminho, operacoes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Salvar .dst editado
    dst_editado_nome = f"{uuid.uuid4().hex[:8]}_edit.dst"
    dst_editado_path = os.path.join(_ARTEFATOS, dst_editado_nome)
    salvar_pattern(resultado["pattern"], dst_editado_path)

    # Salvar SVG
    svg_nome = f"{uuid.uuid4().hex[:8]}_edit.svg"
    svg_path = os.path.join(_ARTEFATOS, svg_nome)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(resultado["svg"])

    # Re-validar
    params = job.get("resultado", {}).get("params", {})
    metrics = StitchMetrics(dst_editado_path)
    validacao = run_checklist(metrics, params)

    log.info("editar.concluido", job_id=job_id, operacoes=resultado["operacoes_aplicadas"])

    return {
        "job_id": job_id,
        "dst_editado": dst_editado_nome,
        "preview_svg": svg_nome,
        "stats_original": resultado["stats_original"],
        "stats_editado": resultado["stats_editado"],
        "operacoes_aplicadas": resultado["operacoes_aplicadas"],
        "validacao": validacao,
    }


@app.get("/v1/pedido/{job_id}/validacoes")
def obter_validacoes(job_id: str):
    """Retorna os 11 itens do checklist para o job."""
    job = fila.obter_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")
    itens = fila.obter_validacoes(job_id)
    return {"job_id": job_id, "itens": itens, "total": len(itens)}


@app.get("/v1/pedido/{job_id}/laudo")
def gerar_laudo_endpoint(job_id: str):
    """Gera laudo técnico HTML com resultado da validação.

    Retorna HTML que pode ser impresso como PDF.
    """
    from laudo.gerador import gerar_laudo_html, salvar_laudo

    job = fila.obter_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")
    if job["status"] != fila.STATUS_CONCLUIDO:
        raise HTTPException(status_code=400, detail="Job ainda nao concluido.")

    resultado = job.get("resultado", {})

    # Buscar validações salvas
    itens_validacao = fila.obter_validacoes(job_id)
    if itens_validacao:
        resultado["itens"] = {v["item"]: v for v in itens_validacao}

    # Gerar HTML
    html = gerar_laudo_html(job_id, resultado)

    # Salvar
    laudo_nome = f"laudo_{job_id}.html"
    laudo_path = os.path.join(_ARTEFATOS, laudo_nome)
    salvar_laudo(html, laudo_path)

    log.info("laudo.gerado", job_id=job_id)

    return {
        "job_id": job_id,
        "laudo_html": laudo_nome,
        "score_global": resultado.get("score_global"),
        "aprovado": resultado.get("aprovado"),
    }


@app.get("/v1/pedido/{job_id}/laudo/html")
def obter_laudo_html(job_id: str):
    """Retorna o HTML do laudo técnico diretamente."""
    from laudo.gerador import gerar_laudo_html

    job = fila.obter_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")
    if job["status"] != fila.STATUS_CONCLUIDO:
        raise HTTPException(status_code=400, detail="Job ainda nao concluido.")

    resultado = job.get("resultado", {})
    itens_validacao = fila.obter_validacoes(job_id)
    if itens_validacao:
        resultado["itens"] = {v["item"]: v for v in itens_validacao}

    html = gerar_laudo_html(job_id, resultado)
    return Response(content=html, media_type="text/html; charset=utf-8")


# ---------------------------------------------------------------------------
# Billing — Asaas
# ---------------------------------------------------------------------------
class CobrancaRequest(BaseModel):
    """Corpo de POST /v1/billing/criar-cobranca."""

    cliente_email: str
    cliente_nome: str
    plano: str = "avulso"
    tipo: str = "PIX"


@app.get("/v1/billing/planos")
def obter_planos():
    """Retorna planos disponíveis."""
    from infra.billing import listar_planos
    return listar_planos()


@app.post("/v1/billing/criar-cobranca")
def criar_cobranca_endpoint(
    payload: CobrancaRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Cria cobrança no Asaas (Pix/Boleto)."""
    from infra.billing import criar_cobranca, PLANOS

    plano = PLANOS.get(payload.plano)
    if not plano:
        raise HTTPException(status_code=400, detail=f"Plano '{payload.plano}' invalido.")

    resultado = criar_cobranca(
        cliente_email=payload.cliente_email,
        cliente_nome=payload.cliente_nome,
        valor=plano["preco"],
        descricao=f"StitchGuard - {plano['nome']} - {plano['descricao']}",
        tipo=payload.tipo,
    )

    if not resultado.get("ok"):
        raise HTTPException(status_code=502, detail=resultado.get("error", "Erro ao criar cobranca"))

    log.info("billing.criada", user_id=current_user.id, plano=payload.plano)

    return {
        "cobranca_id": resultado["cobranca_id"],
        "status": resultado["status"],
        "plano": plano,
        "payload": resultado.get("payload"),
    }


@app.get("/v1/billing/status/{cobranca_id}")
def verificar_status_endpoint(cobranca_id: str):
    """Verifica status de uma cobrança."""
    from infra.billing import verificar_status

    resultado = verificar_status(cobranca_id)
    if not resultado.get("ok"):
        raise HTTPException(status_code=502, detail=resultado.get("error", "Erro ao verificar status"))

    return resultado


@app.post("/v1/billing/webhook")
async def billing_webhook(request: Request):
    """Recebe notificação webhook do Asaas."""
    from infra.billing import processar_webhook

    payload = await request.json()
    resultado = processar_webhook(payload)

    log.info("billing.webhook_recebido", resultado=resultado)

    return resultado


# ---------------------------------------------------------------------------
# Feedback do Cliente
# ---------------------------------------------------------------------------
class FeedbackRequest(BaseModel):
    """Corpo de POST /v1/pedido/{id}/feedback."""

    aprovado: bool
    observacoes: str | None = None


@app.post("/v1/pedido/{job_id}/aprovar")
def aprovar_pedido(job_id: str):
    """Cliente aprova a matriz entregue."""
    job = fila.obter_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")

    # Atualizar status do job
    fila.atualizar_status(job_id, job["status"], resultado={
        **(job.get("resultado") or {}),
        "aprovado_cliente": True,
    })

    log.info("feedback.aprovado", job_id=job_id)

    return {"job_id": job_id, "aprovado": True}


@app.post("/v1/pedido/{job_id}/rejeitar")
def rejeitar_pedido(job_id: str, payload: FeedbackRequest):
    """Cliente rejeita a matriz com observações."""
    job = fila.obter_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")

    # Atualizar status do job
    fila.atualizar_status(job_id, job["status"], resultado={
        **(job.get("resultado") or {}),
        "aprovado_cliente": False,
        "observacoes_cliente": payload.observacoes,
    })

    log.info("feedback.rejeitado", job_id=job_id, obs=payload.observacoes)

    return {"job_id": job_id, "aprovado": False, "observacoes": payload.observacoes}


@app.get("/v1/pedido/{job_id}/feedback")
def obter_feedback(job_id: str):
    """Retorna feedback do cliente sobre a matriz."""
    job = fila.obter_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")

    resultado = job.get("resultado") or {}
    return {
        "job_id": job_id,
        "aprovado_cliente": resultado.get("aprovado_cliente"),
        "observacoes_cliente": resultado.get("observacoes_cliente"),
    }


# ---------------------------------------------------------------------------
# Notificações — E-mail + Webhooks
# ---------------------------------------------------------------------------
class NotificarRequest(BaseModel):
    """Corpo de POST /v1/notificar/enviar."""

    destinatario: str
    nome_cliente: str
    job_id: str
    valor: float | None = None
    plano: str | None = None


@app.post("/v1/notificar/enviar")
def enviar_notificacao(
    payload: NotificarRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Envia e-mail de entrega da matriz."""
    from infra.notificacoes import enviar_email_entrega

    download_url = f"{BASE_URL}/v1/artefatos/{payload.job_id}"

    resultado = enviar_email_entrega(
        destinatario=payload.destinatario,
        nome_cliente=payload.nome_cliente,
        job_id=payload.job_id,
        download_url=download_url,
        valor=payload.valor,
        plano=payload.plano,
    )

    if not resultado.get("ok"):
        raise HTTPException(status_code=502, detail=resultado.get("error", "Erro ao enviar e-mail"))

    log.info("notificacao.enviada", job_id=payload.job_id, destinatario=payload.destinatario)

    return resultado


@app.post("/v1/notificar/webhook-typeform")
async def webhook_typeform(request: Request):
    """Recebe webhook do Typeform/Google Forms e cria pedido automaticamente."""
    from infra.notificacoes import processar_webhook_typeform, criar_pedido_de_webhook

    payload = await request.json()
    dados = processar_webhook_typeform(payload)

    if not dados.get("ok"):
        raise HTTPException(status_code=400, detail="Dados inválidos")

    # Criar pedido automaticamente
    resultado = criar_pedido_de_webhook(dados)

    return {
        "ok": True,
        "job_id": resultado.get("job_id"),
        "mensagem": f"Pedido criado para {dados.get('nome', 'cliente')}",
    }


# ---------------------------------------------------------------------------
# Entrega — Google Drive
# ---------------------------------------------------------------------------
class UploadDriveRequest(BaseModel):
    """Corpo de POST /v1/entrega/upload."""

    job_id: str
    nome_cliente: str


class LinkDownloadRequest(BaseModel):
    """Corpo de POST /v1/entrega/link."""

    job_id: str
    expiracao_horas: int = 24


@app.post("/v1/entrega/upload")
def upload_drive(
    payload: UploadDriveRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Upload de arquivo para Google Drive."""
    from infra.entrega import upload_para_drive
    from infra.storage import Job

    job = fila.obter_job(payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")

    dst_nome = job.get("resultado", {}).get("dst")
    if not dst_nome:
        raise HTTPException(status_code=400, detail="Arquivo .dst nao encontrado.")

    dst_path = os.path.join(_ARTEFATOS, dst_nome)
    if not os.path.exists(dst_path):
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado no disco.")

    resultado = upload_para_drive(
        arquivo_path=dst_path,
        nome_cliente=payload.nome_cliente,
        job_id=payload.job_id,
    )

    if not resultado.get("ok"):
        raise HTTPException(status_code=502, detail=resultado.get("error", "Erro ao upload"))

    log.info("entrega.upload", job_id=payload.job_id, file_id=resultado.get("file_id"))

    return resultado


@app.post("/v1/entrega/link")
def gerar_link(
    payload: LinkDownloadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Gera link de download temporário."""
    from infra.entrega import gerar_link_download

    job = fila.obter_job(payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")

    resultado = gerar_link_download(
        job_id=payload.job_id,
        expiracao_horas=payload.expiracao_horas,
    )

    return resultado


@app.get("/v1/entrega/arquivos/{nome_cliente}")
def listar_arquivos(nome_cliente: str):
    """Lista arquivos de um cliente no Drive."""
    from infra.entrega import listar_arquivos_cliente

    resultado = listar_arquivos_cliente(nome_cliente)
    return resultado


# ---------------------------------------------------------------------------
# Configuração BASE_URL
# ---------------------------------------------------------------------------
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
