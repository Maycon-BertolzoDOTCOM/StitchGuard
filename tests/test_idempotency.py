"""Testes de idempotencia (POST /v1/pedido)."""
import time
import uuid

from fastapi.testclient import TestClient

from application.main import app

client = TestClient(app)


def _get_token():
    r = client.post("/v1/auth/register", json={
        "email": f"idem_{uuid.uuid4().hex[:8]}@test.com",
        "username": f"idem_{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    return r.json()["access_token"]


def _auth_header():
    return {"Authorization": f"Bearer {_get_token()}"}


def test_pedido_idempotente():
    """Mesmo payload retorna o mesmo job_id (REPLAY)."""
    unique = uuid.uuid4().hex[:8]
    payload = {"tecido": "jeans", "maquina": "tajima-tfmx-6", "arte": f"idem_{unique}"}
    headers = _auth_header()
    r1 = client.post("/v1/pedido", json=payload, headers=headers)
    assert r1.status_code == 202
    jid1 = r1.json()["job_id"]

    r2 = client.post("/v1/pedido", json=payload, headers=headers)
    assert r2.status_code == 202
    jid2 = r2.json()["job_id"]

    assert jid1 == jid2
    assert r2.headers.get("X-Idempotency") == "REPLAY"


def test_pedido_diferente_payload():
    """Payloads diferentes geram jobs diferentes."""
    headers = _auth_header()
    unique = uuid.uuid4().hex[:8]
    r1 = client.post("/v1/pedido", json={"tecido": "jeans", "arte": f"jeans_{unique}"}, headers=headers)
    r2 = client.post("/v1/pedido", json={"tecido": "nylon", "arte": f"nylon_{unique}"}, headers=headers)
    assert r1.json()["job_id"] != r2.json()["job_id"]
    assert r2.headers.get("X-Idempotency") != "REPLAY"


def test_idempotency_header_ausente_no_primeiro():
    """Primeira requisicao nao tem header X-Idempotency."""
    unique = uuid.uuid4().hex[:8]
    payload = {"tecido": "bone", "maquina": "singer-xl-400", "arte": f"bone_{unique}"}
    r = client.post("/v1/pedido", json=payload, headers=_auth_header())
    assert "X-Idempotency" not in r.headers
