"""Billing — integração com Asaas (gateway de pagamento brasileiro).

Endpoints:
- POST /v1/billing/criar-cobranca → cria cobrança (Pix/Boleto)
- GET /v1/billing/status/{id} → verifica status do pagamento
- POST /v1/billing/webhook → recebe notificação do Asaas

Referência: https://docs.asaas.com/
"""
import os
from datetime import datetime, timedelta, timezone

import httpx
import structlog

log = structlog.get_logger()

# Configuração do Asaas
ASAAS_API_URL = os.environ.get("ASAAS_API_URL", "https://api.asaas.com/v3")
ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "")

# Planos
PLANOS = {
    "bronze": {
        "nome": "Plano Bronze",
        "matrizes": 5,
        "preco": 497.00,
        "descricao": "5 matrizes/mês",
    },
    "prata": {
        "nome": "Plano Prata",
        "matrizes": 15,
        "preco": 997.00,
        "descricao": "15 matrizes/mês",
    },
    "ouro": {
        "nome": "Plano Ouro",
        "matrizes": 50,
        "preco": 2497.00,
        "descricao": "50 matrizes/mês",
    },
    "avulso": {
        "nome": "Avulso (Urgente)",
        "matrizes": 1,
        "preco": 150.00,
        "descricao": "1 matriz urgente",
    },
}


def _headers() -> dict:
    """Headers para requisições ao Asaas."""
    return {
        "access_token": ASAAS_API_KEY,
        "Content-Type": "application/json",
    }


def criar_cobranca(
    cliente_email: str,
    cliente_nome: str,
    valor: float,
    descricao: str,
    vencimento_dias: int = 3,
    tipo: str = "PIX",
) -> dict:
    """Cria cobrança no Asaas.

    Args:
        cliente_email: e-mail do cliente
        cliente_nome: nome do cliente
        valor: valor em R$
        descricao: descrição da cobrança
        vencimento_dias: dias para vencimento
        tipo: PIX, BOLETO ou CREDIT_CARD

    Returns:
        dict com id, status, payload de pagamento
    """
    if not ASAAS_API_KEY:
        # Modo stub (desenvolvimento)
        log.warning("billing.stub", cliente=cliente_email, valor=valor)
        return {
            "ok": True,
            "stub": True,
            "cobranca_id": f"stub_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "status": "PENDING",
            "payload": {
                "paymentUrl": f"https://sandbox.asaas.com/pix/stub",
                "pixQrCode": "stub_qr_code",
            },
        }

    vencimento = (datetime.now(timezone.utc) + timedelta(days=vencimento_dias)).strftime("%Y-%m-%d")

    payload = {
        "customer": cliente_email,
        "billingType": tipo,
        "value": valor,
        "dueDate": vencimento,
        "description": descricao,
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{ASAAS_API_URL}/payments",
                headers=_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            log.info(
                "billing.criada",
                cobranca_id=data.get("id"),
                valor=valor,
                tipo=tipo,
            )

            return {
                "ok": True,
                "cobranca_id": data.get("id"),
                "status": data.get("status"),
                "payload": data,
            }
    except httpx.HTTPStatusError as e:
        log.error("billing.erro_http", status=e.response.status_code, detail=e.response.text[:200])
        return {"ok": False, "error": f"Erro HTTP {e.response.status_code}"}
    except Exception as e:
        log.error("billing.erro", erro=str(e))
        return {"ok": False, "error": str(e)}


def verificar_status(cobranca_id: str) -> dict:
    """Verifica status de uma cobrança.

    Returns:
        dict com status (PENDING, CONFIRMED, OVERDUE, etc.)
    """
    if not ASAAS_API_KEY:
        return {
            "ok": True,
            "stub": True,
            "cobranca_id": cobranca_id,
            "status": "CONFIRMED",
        }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{ASAAS_API_URL}/payments/{cobranca_id}",
                headers=_headers(),
            )
            response.raise_for_status()
            data = response.json()

            return {
                "ok": True,
                "cobranca_id": cobranca_id,
                "status": data.get("status"),
                "payload": data,
            }
    except Exception as e:
        log.error("billing.verificar_erro", erro=str(e))
        return {"ok": False, "error": str(e)}


def processar_webhook(payload: dict) -> dict:
    """Processa notificação webhook do Asaas.

    Eventos suportados:
    - PAYMENT_RECEIVED: pagamento confirmado
    - PAYMENT_OVERDUE: pagamento atrasado
    """
    event = payload.get("event")
    payment = payload.get("payment", {})

    cobranca_id = payment.get("id")
    status = payment.get("status")

    log.info(
        "billing.webhook",
        webhook_event=event,
        cobranca_id=cobranca_id,
        status=status,
    )

    if event == "PAYMENT_RECEIVED":
        # Pagamento confirmado — liberar serviço
        return {
            "ok": True,
            "acao": "liberar_servico",
            "cobranca_id": cobranca_id,
            "cliente": payment.get("customer"),
            "valor": payment.get("value"),
        }
    elif event == "PAYMENT_OVERDUE":
        # Pagamento atrasado — bloquear serviço
        return {
            "ok": True,
            "acao": "bloquear_servico",
            "cobranca_id": cobranca_id,
        }

    return {"ok": True, "acao": "nenhuma", "event": event}


def listar_planos() -> dict:
    """Retorna planos disponíveis."""
    return {
        "planos": PLANOS,
        "moeda": "BRL",
    }
