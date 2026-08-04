"""Integracao com Asaas API (assinaturas recorrentes + webhook)."""


def criar_cobranca(cliente_id: str, valor: float, descricao: str) -> str:
    """Cria cobranca/assinatura no Asaas e retorna o ID.

    Endpoints: POST /subscriptions, GET /subscriptions/{id}/paymentLink.
    """
    raise NotImplementedError("Integracao com Asaas pendente.")


def webhook(payload: dict) -> None:
    """Processa evento do Asaas.

    Validar ASAAS_WEBHOOK_SECRET (timing-safe compare) e deduplicar paymentId
    — licao SEC-07 do MaterialView-Pro.
    """
    raise NotImplementedError("Webhook Asaas pendente.")
