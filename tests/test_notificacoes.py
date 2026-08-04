"""Testes do módulo de notificações."""
from infra.notificacoes import (
    enviar_email_entrega,
    processar_webhook_typeform,
    criar_pedido_de_webhook,
)


class TestEnviarEmailEntrega:
    def test_stub_sem_smtp(self):
        """Sem SMTP configurado, retorna stub."""
        result = enviar_email_entrega(
            destinatario="test@test.com",
            nome_cliente="João",
            job_id="abc123",
            download_url="https://example.com/download/abc123",
        )
        assert result["ok"] is True
        assert result["stub"] is True
        assert result["destinatario"] == "test@test.com"

    def test_com_plano_e_valor(self):
        result = enviar_email_entrega(
            destinatario="test@test.com",
            nome_cliente="João",
            job_id="abc123",
            download_url="https://example.com/download/abc123",
            valor=997.00,
            plano="Prata",
        )
        assert result["ok"] is True


class TestProcessarWebhookTypeform:
    def test_processar_dados_completos(self):
        payload = {
            "answers": [
                {"field": {"ref": "nome"}, "text": "João Silva"},
                {"field": {"ref": "email"}, "email": "joao@test.com"},
                {"field": {"ref": "whatsapp"}, "text": "+5511999999999"},
                {"field": {"ref": "arte"}, "file_url": "https://example.com/arte.png"},
                {"field": {"ref": "tecido"}, "choice": {"label": "Jeans"}},
                {"field": {"ref": "prazo"}, "choice": {"label": "Normal (24h)"}},
            ]
        }
        result = processar_webhook_typeform(payload)
        assert result["ok"] is True
        assert result["nome"] == "João Silva"
        assert result["email"] == "joao@test.com"
        assert result["tecido"] == "Jeans"

    def test_processar_dados_parciais(self):
        payload = {"answers": []}
        result = processar_webhook_typeform(payload)
        assert result["ok"] is True
        assert result["nome"] == ""


class TestCriarPedidoDeWebhook:
    def test_cria_pedido(self):
        dados = {
            "nome": "João Silva",
            "email": "joao@test.com",
            "arte_url": "https://example.com/arte.png",
            "tecido": "Jeans",
        }
        result = criar_pedido_de_webhook(dados)
        assert result["ok"] is True
        assert "job_id" in result
        assert result["status"] == "pendente"
