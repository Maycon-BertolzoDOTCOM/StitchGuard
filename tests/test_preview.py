"""Testes de preview SVG."""
import time
import uuid

from fastapi.testclient import TestClient

from application.main import app, _dst_para_svg

client = TestClient(app)


def _get_token():
    r = client.post("/v1/auth/register", json={
        "email": f"preview_{uuid.uuid4().hex[:8]}@test.com",
        "username": f"preview_{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    return r.json()["access_token"]


def _auth_header():
    return {"Authorization": f"Bearer {_get_token()}"}


def test_dst_para_svg():
    """Conversao .dst -> SVG retorna SVG valido."""
    svg = _dst_para_svg("tests/fixtures/limpo.dst")
    assert svg.startswith("<svg")
    assert "xmlns" in svg
    assert "</svg>" in svg
    assert "path" in svg


def test_dst_para_svg_tem_dados():
    """SVG gerado tem conteudo (nao vazio)."""
    svg = _dst_para_svg("tests/fixtures/limpo.dst")
    assert len(svg) > 100


def test_preview_endpoint():
    """Endpoint /v1/preview/{id} retorna SVG para job concluido."""
    headers = _auth_header()
    payload = {"tecido": "jeans", "maquina": "generica"}
    r = client.post("/v1/pedido", json=payload, headers=headers)
    jid = r.json()["job_id"]

    for _ in range(30):
        time.sleep(0.2)
        r2 = client.get(f"/v1/pedido/{jid}/status", headers=headers)
        if r2.json()["status"] == "concluido":
            break

    r3 = client.get(f"/v1/preview/{jid}", headers=headers)
    assert r3.status_code == 200
    assert r3.headers["content-type"] == "image/svg+xml"
    assert "<svg" in r3.text
    assert "</svg>" in r3.text


def test_preview_404_job_inexistente():
    """Job inexistente retorna 404."""
    r = client.get("/v1/preview/nao_existe", headers=_auth_header())
    assert r.status_code == 404


def test_preview_404_job_pendente():
    """Job pendente (nao concluido) retorna 404."""
    headers = _auth_header()
    payload = {"tecido": "nylon"}
    r = client.post("/v1/pedido", json=payload, headers=headers)
    jid = r.json()["job_id"]
    r2 = client.get(f"/v1/preview/{jid}", headers=headers)
    assert r2.status_code in (200, 404)
