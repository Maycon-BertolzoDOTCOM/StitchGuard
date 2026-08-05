"""Testes de export multi-formato e novos endpoints."""
import os
import time
import uuid

from fastapi.testclient import TestClient

from application.main import app

client = TestClient(app)


def _get_token():
    r = client.post("/v1/auth/register", json={
        "email": f"test{uuid.uuid4().hex[:6]}@test.com",
        "username": f"testuser{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    return r.json()["access_token"]


def _auth_header():
    return {"Authorization": f"Bearer {_get_token()}"}


def _criar_job_concluido():
    headers = _auth_header()
    r = client.post("/v1/pedido", json={"tecido": "jeans", "maquina": "tajima-tfmx-6"}, headers=headers)
    job_id = r.json()["job_id"]
    for _ in range(40):
        time.sleep(0.05)
        st = client.get(f"/v1/pedido/{job_id}/status", headers=headers).json()
        if st["status"] in ("concluido", "erro"):
            break
    return job_id, headers


class TestExportMultiFormato:
    def test_export_pes(self):
        job_id, headers = _criar_job_concluido()
        r = client.post(f"/v1/pedido/{job_id}/exportar", json={"formato": "pes"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["formato"] == "pes"
        assert r.json()["arquivo"].endswith(".pes")

    def test_export_exp(self):
        job_id, headers = _criar_job_concluido()
        r = client.post(f"/v1/pedido/{job_id}/exportar", json={"formato": "exp"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["formato"] == "exp"

    def test_export_vp3(self):
        job_id, headers = _criar_job_concluido()
        r = client.post(f"/v1/pedido/{job_id}/exportar", json={"formato": "vp3"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["formato"] == "vp3"

    def test_export_xxx(self):
        job_id, headers = _criar_job_concluido()
        r = client.post(f"/v1/pedido/{job_id}/exportar", json={"formato": "xxx"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["formato"] == "xxx"

    def test_export_invalido(self):
        job_id, headers = _criar_job_concluido()
        r = client.post(f"/v1/pedido/{job_id}/exportar", json={"formato": "xyz"}, headers=headers)
        assert r.status_code == 400

    def test_export_job_inexistente(self):
        headers = _auth_header()
        r = client.post("/v1/pedido/naoexiste/exportar", json={"formato": "pes"}, headers=headers)
        assert r.status_code == 404


class TestFormatos:
    def test_listar_formatos(self):
        r = client.get("/v1/formatos")
        assert r.status_code == 200
        assert "dst" in r.json()["formatos"]
        assert "pes" in r.json()["formatos"]
        assert "exp" in r.json()["formatos"]


class TestUploadDst:
    def test_upload_dst_direto(self):
        headers = _auth_header()
        with open("tests/fixtures/limpo.dst", "rb") as f:
            r = client.post(
                "/v1/upload",
                files={"arquivo": ("limpo.dst", f, "application/octet-stream")},
                headers=headers,
            )
        assert r.status_code == 200
        assert "dst" in r.json()
        assert "validacao" in r.json()
        assert r.json()["resumo"]["stitches"] > 0


class TestLettering:
    def test_lettering_basico(self):
        headers = _auth_header()
        r = client.post("/v1/lettering", json={
            "texto": "OLA",
            "fonte": "block",
            "tamanho_mm": 15.0,
        }, headers=headers)
        assert r.status_code == 200
        assert r.json()["texto"] == "OLA"
        assert r.json()["fonte"] == "block"
        assert r.json()["resumo"]["stitches"] > 0

    def test_lettering_script(self):
        headers = _auth_header()
        r = client.post("/v1/lettering", json={
            "texto": "BORDADO",
            "fonte": "script",
        }, headers=headers)
        assert r.status_code == 200
        assert r.json()["fonte"] == "script"

    def test_lettering_fonte_invalida(self):
        headers = _auth_header()
        r = client.post("/v1/lettering", json={
            "texto": "TESTE",
            "fonte": "invalida",
        }, headers=headers)
        assert r.status_code == 400

    def test_lettering_texto_vazio(self):
        headers = _auth_header()
        r = client.post("/v1/lettering", json={
            "texto": "   ",
            "fonte": "block",
        }, headers=headers)
        assert r.status_code == 400

    def test_listar_fontes(self):
        r = client.get("/v1/fontes")
        assert r.status_code == 200
        assert "block" in r.json()["fontes"]
        assert "script" in r.json()["fontes"]
        assert "bold" in r.json()["fontes"]


class TestBatch:
    def test_batch_upload(self):
        headers = _auth_header()
        with open("tests/fixtures/limpo.dst", "rb") as f1, \
             open("tests/fixtures/limpo.dst", "rb") as f2:
            r = client.post(
                "/v1/batch",
                files=[
                    ("arquivos", ("teste1.dst", f1, "application/octet-stream")),
                    ("arquivos", ("teste2.dst", f2, "application/octet-stream")),
                ],
                data={"tecido": "jeans", "formato": "dst"},
                headers=headers,
            )
        assert r.status_code == 200
        assert r.json()["total"] == 2
        assert r.json()["processados"] == 2

    def test_batch_formato_invalido(self):
        headers = _auth_header()
        r = client.post(
            "/v1/batch",
            files=[("arquivos", ("teste.txt", b"conteudo", "text/plain"))],
            headers=headers,
        )
        assert r.status_code == 400  # Nenhum arquivo válido


class TestDashboard:
    def test_dashboard(self):
        headers = _auth_header()
        r = client.get("/v1/dashboard", headers=headers)
        assert r.status_code == 200
        assert "estatisticas" in r.json()
        assert "ultimos_jobs" in r.json()

    def test_dashboard_sem_auth(self):
        r = client.get("/v1/dashboard")
        assert r.status_code == 401
