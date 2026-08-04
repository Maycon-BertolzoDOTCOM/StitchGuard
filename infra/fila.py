"""Fila de jobs — SQLAlchemy (SQLite dev, PostgreSQL prod).

Persiste o estado de cada job (pendente/processando/concluido/erro) no banco,
permitindo polling e rastreabilidade reais via API.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select

from infra.storage import Job, Validacao, SessionLocal, init_db

log = structlog.get_logger()

init_db()

STATUS_PENDENTE = "pendente"
STATUS_PROCESSANDO = "processando"
STATUS_CONCLUIDO = "concluido"
STATUS_ERRO = "erro"

IDEMPOTENCY_TTL_HORAS = 24


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_dict(job: Job) -> dict:
    return {
        "job_id": job.id,
        "status": job.status,
        "params": json.loads(job.params) if job.params else {},
        "resultado": json.loads(job.resultado) if job.resultado else None,
        "erro": job.erro,
        "criado_em": job.criado_em,
        "atualizado_em": job.atualizado_em,
    }


def calcular_hash(arte: str | None, params: dict) -> str:
    """Computa SHA-256 de (arte + params) para idempotencia."""
    payload = json.dumps({"arte": arte, "params": params}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def obter_por_hash(content_hash: str) -> dict | None:
    """Busca job existente pelo hash de conteudo (idempotencia).

    Retorna None se nao encontrado ou se o job expirou (> 24h).
    """
    with SessionLocal() as session:
        job = session.execute(
            select(Job).where(Job.content_hash == content_hash).order_by(Job.criado_em.desc()).limit(1)
        ).scalar_one_or_none()
        if job is None:
            return None
        # Verifica TTL
        try:
            criado = datetime.fromisoformat(job.criado_em)
            if datetime.now(timezone.utc) - criado > timedelta(hours=IDEMPOTENCY_TTL_HORAS):
                return None
        except (ValueError, TypeError):
            return None
        return _to_dict(job)


def enfileirar(job_id: str, arte: str | None, params: dict, content_hash: str | None = None) -> None:
    """Adiciona job a fila (status pendente)."""
    agora = _agora()
    with SessionLocal() as session:
        session.add(Job(
            id=job_id,
            status=STATUS_PENDENTE,
            content_hash=content_hash,
            arte=arte,
            params=json.dumps(params, ensure_ascii=False),
            criado_em=agora,
            atualizado_em=agora,
        ))
        session.commit()
    log.info("fila.enfileirar", job_id=job_id, hash=content_hash[:8] if content_hash else None)


def obter_proximo() -> dict | None:
    """Pega o proximo job pendente (mais antigo)."""
    with SessionLocal() as session:
        job = session.execute(
            select(Job).where(Job.status == STATUS_PENDENTE).order_by(Job.criado_em).limit(1)
        ).scalar_one_or_none()
        return _to_dict(job) if job else None


def obter_job(job_id: str) -> dict | None:
    """Retorna o job por id (None se nao existir)."""
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        return _to_dict(job) if job else None


def atualizar_status(job_id: str, status: str, resultado: dict | None = None, erro: str | None = None) -> None:
    """Atualiza status/resultado de um job."""
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        if job is None:
            return
        job.status = status
        job.atualizado_em = _agora()
        if resultado is not None:
            job.resultado = json.dumps(resultado, ensure_ascii=False)
        if erro is not None:
            job.erro = erro
        session.commit()
    log.info("fila.status", job_id=job_id, status=status)


def salvar_validacoes(job_id: str, itens: dict) -> None:
    """Persiste os 11 itens do checklist no banco."""
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
    log.info("fila.validacoes", job_id=job_id, itens=len(itens))


def obter_validacoes(job_id: str) -> list[dict]:
    """Retorna as validacoes de um job."""
    with SessionLocal() as session:
        rows = session.execute(
            select(Validacao).where(Validacao.job_id == job_id).order_by(Validacao.id)
        ).scalars().all()
        return [
            {"item": v.item, "score": v.score, "aprovado": v.aprovado, "detalhe": v.detalhe}
            for v in rows
        ]
