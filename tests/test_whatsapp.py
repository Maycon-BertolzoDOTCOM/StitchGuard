"""Testes para WhatsApp e batch processing."""
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


class TestWhatsApp:
    def testEnviarWhatsAppStub(self):
        headers = _auth_header()
        r = client.post("/v1/notificar/whatsapp", json={
            "telefone": "5511999999999",
            "mensagem": "Teste",
            "tipo": "entrega",
        }, headers=headers)
        assert r.status_code == 200
        assert r.json()["stub"] is True

    def testEnviarWhatsAppComJob(self):
        headers = _auth_header()
        r = client.post("/v1/notificar/whatsapp", json={
            "telefone": "5511999999999",
            "job_id": "abc123",
            "tipo": "entrega",
        }, headers=headers)
        assert r.status_code == 200
        assert r.json()["stub"] is True

    def testEnviarWhatsAppSemAuth(self):
        r = client.post("/v1/notificar/whatsapp", json={
            "telefone": "5511999999999",
            "mensagem": "Teste",
        })
        assert r.status_code == 401

    def testWebhookWhatsApp(self):
        r = client.post("/v1/notificar/whatsapp-webhook", json={
            "message": {
                "from": "5511999999999",
                "text": "status",
            }
        })
        assert r.status_code == 200
        assert r.json()["auto_resposta"] is True

    def testWebhookWhatsAppObrigado(self):
        r = client.post("/v1/notificar/whatsapp-webhook", json={
            "message": {
                "from": "5511999999999",
                "text": "obrigado",
            }
        })
        assert r.status_code == 200
        assert r.json()["auto_resposta"] is True
