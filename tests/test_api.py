"""Testes de regressao da API L1 (FastAPI) usando TestClient."""
import os
import time

from fastapi.testclient import TestClient

from application.main import app
from infra import fila
from infra.storage import SessionLocal, Job

client = TestClient(app)

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "limpo.dst")


def _get_token():
    """Registra usuario de teste e retorna token."""
    import uuid
    r = client.post("/v1/auth/register", json={
        "email": f"test{uuid.uuid4().hex[:6]}@test.com",
        "username": f"testuser{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    return r.json()["access_token"]


def _auth_header():
    return {"Authorization": f"Bearer {_get_token()}"}


def _poll(job_id, tentativas=40):
    for _ in range(tentativas):
        st = client.get(f"/v1/pedido/{job_id}/status", headers=_auth_header()).json()
        if st["status"] in ("concluido", "erro"):
            return st
        time.sleep(0.05)
    raise AssertionError("job nao concluiu a tempo")


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_catalogo():
    assert client.get("/v1/maquinas").status_code == 200
    assert "tajima-tfmx-6" in client.get("/v1/maquinas").json()["ids"]
    assert "malha" in client.get("/v1/presets").json()["presets"]


def test_validar_fixture_aprovado():
    with open(FIXTURE, "rb") as fh:
        r = client.post(
            "/v1/validar",
            files={"arquivo": ("limpo.dst", fh, "application/octet-stream")},
            data={"tecido": "nylon", "compensacao": "media", "underlay": "true", "maquina": "generica"},
        )
    assert r.status_code == 200
    assert r.json()["aprovado"] is True
    assert r.json()["score_global"] >= 0.85


def test_validar_rejeito_extensao():
    r = client.post(
        "/v1/validar",
        files={"arquivo": ("arte.txt", b"x", "text/plain")},
    )
    assert r.status_code == 400


def test_pedido_amostra_persistente():
    r = client.post("/v1/pedido", json={"tecido": "jeans", "maquina": "tajima-tfmx-6"}, headers=_auth_header())
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    st = _poll(job_id)
    assert st["status"] == "concluido"
    assert st["resultado"]["aprovado"] is True
    assert st["resultado"].get("dst")

    dl = client.get(f"/v1/artefatos/{job_id}", headers=_auth_header())
    assert dl.status_code == 200
    assert dl.content

    with SessionLocal() as s:
        existe = s.get(Job, job_id) is not None
    assert existe


def test_pedido_404():
    assert client.get("/v1/pedido/naoexiste/status", headers=_auth_header()).status_code == 404
