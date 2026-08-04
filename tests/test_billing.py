"""Testes do módulo de billing."""
from infra.billing import (
    criar_cobranca,
    verificar_status,
    processar_webhook,
    listar_planos,
    PLANOS,
)


class TestPlanos:
    def test_listar_planos(self):
        result = listar_planos()
        assert "planos" in result
        assert "bronze" in result["planos"]
        assert "prata" in result["planos"]
        assert "ouro" in result["planos"]
        assert "avulso" in result["planos"]

    def test_precos_planos(self):
        assert PLANOS["bronze"]["preco"] == 497.00
        assert PLANOS["prata"]["preco"] == 997.00
        assert PLANOS["ouro"]["preco"] == 2497.00
        assert PLANOS["avulso"]["preco"] == 150.00

    def test_matrizes_planos(self):
        assert PLANOS["bronze"]["matrizes"] == 5
        assert PLANOS["prata"]["matrizes"] == 15
        assert PLANOS["ouro"]["matrizes"] == 50
        assert PLANOS["avulso"]["matrizes"] == 1


class TestCriarCobranca:
    def test_stub_sem_api_key(self):
        """Sem API key, retorna stub."""
        result = criar_cobranca(
            cliente_email="test@test.com",
            cliente_nome="Teste",
            valor=100.0,
            descricao="Teste",
        )
        assert result["ok"] is True
        assert result["stub"] is True
        assert "cobranca_id" in result

    def test_retorna_status_pending(self):
        result = criar_cobranca(
            cliente_email="test@test.com",
            cliente_nome="Teste",
            valor=100.0,
            descricao="Teste",
        )
        assert result["status"] == "PENDING"


class TestVerificarStatus:
    def test_stub_sem_api_key(self):
        result = verificar_status("stub_123")
        assert result["ok"] is True
        assert result["stub"] is True
        assert result["status"] == "CONFIRMED"


class TestProcessarWebhook:
    def test_pagamento_recebido(self):
        payload = {
            "event": "PAYMENT_RECEIVED",
            "payment": {
                "id": "pay_123",
                "status": "CONFIRMED",
                "customer": "test@test.com",
                "value": 997.00,
            },
        }
        result = processar_webhook(payload)
        assert result["ok"] is True
        assert result["acao"] == "liberar_servico"
        assert result["cobranca_id"] == "pay_123"

    def test_pagamento_atrasado(self):
        payload = {
            "event": "PAYMENT_OVERDUE",
            "payment": {
                "id": "pay_456",
                "status": "OVERDUE",
            },
        }
        result = processar_webhook(payload)
        assert result["ok"] is True
        assert result["acao"] == "bloquear_servico"

    def test_evento_desconhecido(self):
        payload = {
            "event": "UNKNOWN_EVENT",
            "payment": {"id": "pay_789"},
        }
        result = processar_webhook(payload)
        assert result["ok"] is True
        assert result["acao"] == "nenhuma"
