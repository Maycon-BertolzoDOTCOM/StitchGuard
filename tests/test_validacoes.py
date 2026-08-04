"""Testes de persistencia de validacoes."""
import time
import uuid

from fastapi.testclient import TestClient

from application.main import app
from infra import fila
from infra.storage import SessionLocal, Validacao, init_db

client = TestClient(app)


def _get_token():
    r = client.post("/v1/auth/register", json={
        "email": f"validacoes_{uuid.uuid4().hex[:8]}@test.com",
        "username": f"validacoes_{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    return r.json()["access_token"]


def _auth_header():
    return {"Authorization": f"Bearer {_get_token()}"}


def _unique_job_id(prefix: str = "test_val") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_salvar_validacoes_persiste_no_banco():
    """salvar_validacoes() persiste itens no banco."""
    init_db()
    jid = _unique_job_id()
    fila.enfileirar(jid, None, {"tecido": "jeans"})
    itens = {
        "compensacao": {"score": 1.0, "aprovado": True, "detalhe": "ok"},
        "underlay": {"score": 1.0, "aprovado": True, "detalhe": "ok"},
    }
    fila.salvar_validacoes(jid, itens)
    with SessionLocal() as s:
        rows = s.query(Validacao).filter(Validacao.job_id == jid).all()
        assert len(rows) == 2
        assert rows[0].item == "compensacao"
        assert rows[1].item == "underlay"


def test_obter_validacoes_retorna_lista():
    """obter_validacoes() retorna lista de dicts."""
    jid = _unique_job_id()
    fila.enfileirar(jid, None, {})
    itens = {"densidade": {"score": 0.5, "aprovado": False, "detalhe": "fora da faixa"}}
    fila.salvar_validacoes(jid, itens)
    result = fila.obter_validacoes(jid)
    assert len(result) == 1
    assert result[0]["item"] == "densidade"
    assert result[0]["score"] == 0.5


def test_obter_validacoes_job_sem_validacoes():
    """Job sem validacoes retorna lista vazia."""
    jid = _unique_job_id()
    fila.enfileirar(jid, None, {})
    result = fila.obter_validacoes(jid)
    assert result == []


def test_endpoint_validacoes_404():
    """Endpoint retorna 404 para job inexistente."""
    r = client.get("/v1/pedido/nao_existe/validacoes", headers=_auth_header())
    assert r.status_code == 404


def test_endpoint_validacoes_job_pendente():
    """Job recem-criado pode ja ter validacoes (thread rapida)."""
    headers = _auth_header()
    payload = {"tecido": "jeans"}
    r = client.post("/v1/pedido", json=payload, headers=headers)
    jid = r.json()["job_id"]
    r = client.get(f"/v1/pedido/{jid}/validacoes", headers=headers)
    assert r.status_code == 200
    assert r.json()["total"] in (0, 11)


def test_endpoint_validacoes_apos_conclusao():
    """Apos job concluido via thread, validacoes estao disponiveis."""
    headers = _auth_header()
    payload = {"tecido": "jeans", "maquina": "generica"}
    r = client.post("/v1/pedido", json=payload, headers=headers)
    jid = r.json()["job_id"]
    for _ in range(30):
        time.sleep(0.2)
        r2 = client.get(f"/v1/pedido/{jid}/status", headers=headers)
        if r2.json()["status"] in ("concluido", "erro"):
            break
    r3 = client.get(f"/v1/pedido/{jid}/validacoes", headers=headers)
    assert r3.status_code == 200
    if r2.json()["status"] == "concluido":
        assert r3.json()["total"] == 11
