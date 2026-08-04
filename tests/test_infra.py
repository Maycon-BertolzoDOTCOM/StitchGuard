"""Testes unitários de infra: fila (SQLite) e storage."""
from infra.fila import (
    enfileirar, obter_proximo, obter_job, atualizar_status,
    calcular_hash, obter_por_hash,
    STATUS_PENDENTE, STATUS_PROCESSANDO, STATUS_CONCLUIDO, STATUS_ERRO,
)
from infra.storage import SessionLocal, Job, init_db


def _jid(prefix="t"):
    import uuid
    return f"{prefix}{uuid.uuid4().hex[:6]}"


def _limpar_pendentes():
    with SessionLocal() as s:
        pendentes = s.query(Job).filter(Job.status == STATUS_PENDENTE).all()
        for p in pendentes:
            p.status = "limpeza"
        s.commit()


def test_enfileirar_e_obter():
    jid = _jid()
    enfileirar(jid, None, {"tecido": "jeans"})
    job = obter_job(jid)
    assert job is not None
    assert job["status"] == STATUS_PENDENTE
    assert job["params"]["tecido"] == "jeans"


def test_obter_proximo():
    _limpar_pendentes()
    jid = _jid()
    enfileirar(jid, None, {"tecido": "nylon"})
    prox = obter_proximo()
    assert prox is not None
    assert prox["job_id"] == jid


def test_obter_proximo_vazio():
    _limpar_pendentes()
    assert obter_proximo() is None


def test_atualizar_status_concluido():
    jid = _jid()
    enfileirar(jid, None, {"tecido": "bone"})
    atualizar_status(jid, STATUS_CONCLUIDO, resultado={"score": 1.0})
    job = obter_job(jid)
    assert job["status"] == STATUS_CONCLUIDO
    assert job["resultado"] is not None
    assert job["resultado"]["score"] == 1.0


def test_atualizar_status_erro():
    jid = _jid()
    enfileirar(jid, None, {})
    atualizar_status(jid, STATUS_ERRO, erro="falhou")
    job = obter_job(jid)
    assert job["status"] == STATUS_ERRO
    assert job["erro"] == "falhou"


def test_obter_job_inexistente():
    assert obter_job("nao_existe") is None


def test_atualizar_job_inexistente_nao_crasha():
    atualizar_status("nao_existe", STATUS_CONCLUIDO)


def test_estados_transicoes():
    jid = _jid()
    enfileirar(jid, None, {})
    assert obter_job(jid)["status"] == STATUS_PENDENTE
    atualizar_status(jid, STATUS_PROCESSANDO)
    assert obter_job(jid)["status"] == STATUS_PROCESSANDO
    atualizar_status(jid, STATUS_CONCLUIDO)
    assert obter_job(jid)["status"] == STATUS_CONCLUIDO


def test_init_db_idempotente():
    init_db()
    init_db()


# --- Idempotencia ---

def test_calcular_hash_deterministico():
    h1 = calcular_hash("arte1", {"tecido": "jeans"})
    h2 = calcular_hash("arte1", {"tecido": "jeans"})
    assert h1 == h2
    assert len(h1) == 64  # SHA-256


def test_calcular_hash_diferente_para_diferentes_inputs():
    h1 = calcular_hash("arte1", {"tecido": "jeans"})
    h2 = calcular_hash("arte2", {"tecido": "jeans"})
    h3 = calcular_hash("arte1", {"tecido": "nylon"})
    assert h1 != h2
    assert h1 != h3


def test_obter_por_hash_inexistente():
    assert obter_por_hash("hash_inexistente") is None


def test_enfileirar_com_hash_e_obter_por_hash():
    jid = _jid()
    h = calcular_hash(None, {"tecido": "cetim"})
    enfileirar(jid, None, {"tecido": "cetim"}, content_hash=h)
    job = obter_por_hash(h)
    assert job is not None
    assert job["job_id"] == jid
