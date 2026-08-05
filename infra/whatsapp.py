"""WhatsApp — notificações via WhatsApp Business API.

Para ateliês brasileiros, WhatsApp é o canal #1 de comunicação.

Endpoints:
- POST /v1/notificar/whatsapp → envia mensagem via WhatsApp
- POST /v1/notificar/whatsapp-webhook → recebe mensagens do WhatsApp

Suporta:
- Evolution API (self-hosted, gratuito)
- Meta Cloud API (pago por mensagem)
- Z-API (terceiro)
- Modo stub (desenvolvimento)
"""
import os

import httpx
import structlog

log = structlog.get_logger()

# Configuração WhatsApp
WHATSAPP_PROVIDER = os.environ.get("WHATSAPP_PROVIDER", "stub")  # stub | evolution | meta | zapi
WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "http://localhost:8080")
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")
WHATSAPP_INSTANCE = os.environ.get("WHATSAPP_INSTANCE", "stitchguard")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")  # Meta: Phone Number ID
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")  # Meta: permanent token

# URL base para links
BASE_URL = os.environ.get("BASE_URL", "https://stitchguard.com.br")


def enviar_whatsapp(
    telefone: str,
    mensagem: str,
    nome: str | None = None,
    job_id: str | None = None,
    download_url: str | None = None,
    tipo: str = "entrega",  # entrega | status | cobranca | lembrete
) -> dict:
    """Envia mensagem via WhatsApp.

    Args:
        telefone: número no formato 5511999999999
        mensagem: texto da mensagem
        nome: nome do destinatário (opcional)
        job_id: ID do job (opcional, usado no template)
        download_url: link de download (opcional)
        tipo: tipo da mensagem (entrega/status/cobranca/lembrete)

    Returns:
        dict com status do envio
    """
    # Normalizar telefone (remover +, espaços, traços)
    telefone = telefone.replace("+", "").replace(" ", "").replace("-", "")

    # Construir mensagem formatada se tiver dados do job
    if job_id and download_url:
        mensagem = _montar_mensagem_entrega(
            nome=nome or "Cliente",
            job_id=job_id,
            download_url=download_url,
        )

    log.info("whatsapp.enviando", telefone=telefone, tipo=tipo, provider=WHATSAPP_PROVIDER)

    # Modo stub (desenvolvimento)
    if WHATSAPP_PROVIDER == "stub" or not WHATSAPP_API_TOKEN:
        log.warning("whatsapp.stub", telefone=telefone, tipo=tipo)
        return {
            "ok": True,
            "stub": True,
            "telefone": telefone,
            "tipo": tipo,
            "mensagem_preview": mensagem[:100],
        }

    # Envio real
    try:
        if WHATSAPP_PROVIDER == "evolution":
            return _enviar_evolution(telefone, mensagem)
        elif WHATSAPP_PROVIDER == "meta":
            return _enviar_meta(telefone, mensagem)
        elif WHATSAPP_PROVIDER == "zapi":
            return _enviar_zapi(telefone, mensagem)
        else:
            return {"ok": False, "error": f"Provider desconhecido: {WHATSAPP_PROVIDER}"}
    except Exception as e:
        log.error("whatsapp.erro", erro=str(e), telefone=telefone)
        return {"ok": False, "error": str(e)}


def _montar_mensagem_entrega(nome: str, job_id: str, download_url: str) -> str:
    """Monta mensagem de entrega formatada para WhatsApp."""
    return (
        f"Oi {nome}! 👋\n\n"
        f"✅ Sua matriz de bordado está pronta!\n\n"
        f"📦 *Pedido:* {job_id}\n"
        f"📥 *Download:* {download_url}\n\n"
        f"Basta acessar o link acima para baixar seu arquivo .DST.\n\n"
        f"Se precisar de algum ajuste, é só responder esta mensagem! 😊\n\n"
        f"---\n"
        f"StitchGuard — A Fábrica de Matrizes Autônoma"
    )


def _montar_mensagem_status(nome: str, job_id: str, status: str) -> str:
    """Monta mensagem de status formatada para WhatsApp."""
    status_emoji = {
        "pendente": "⏳",
        "processando": "⚙️",
        "concluido": "✅",
        "erro": "❌",
    }.get(status, "📋")

    return (
        f"Oi {nome}! 👋\n\n"
        f"{status_emoji} *Status do pedido {job_id}:* {status.upper()}\n\n"
        f"Se tiver alguma dúvida, é só responder! 😊"
    )


def _enviar_evolution(telefone: str, mensagem: str) -> dict:
    """Envia via Evolution API (self-hosted)."""
    url = f"{WHATSAPP_API_URL}/message/sendText/{WHATSAPP_INSTANCE}"
    payload = {
        "number": telefone,
        "text": mensagem,
    }
    headers = {"apikey": WHATSAPP_API_TOKEN}

    response = httpx.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    log.info("whatsapp.evolution.enviado", telefone=telefone, key=data.get("key", {}).get("id"))
    return {"ok": True, "provider": "evolution", "message_id": data.get("key", {}).get("id")}


def _enviar_meta(telefone: str, mensagem: str) -> dict:
    """Envia via Meta Cloud API (WhatsApp Business)."""
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "text",
        "text": {"body": mensagem},
    }
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    response = httpx.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    msg_id = data.get("messages", [{}])[0].get("id", "")
    log.info("whatsapp.meta.enviado", telefone=telefone, message_id=msg_id)
    return {"ok": True, "provider": "meta", "message_id": msg_id}


def _enviar_zapi(telefone: str, mensagem: str) -> dict:
    """Envia via Z-API (terceiro brasileiro)."""
    url = f"{WHATSAPP_API_URL}/send-text"
    payload = {
        "phone": telefone,
        "message": mensagem,
    }
    headers = {"Client-Token": WHATSAPP_API_TOKEN}

    response = httpx.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    log.info("whatsapp.zapi.enviado", telefone=telefone)
    return {"ok": True, "provider": "zapi", "message_id": data.get("id", "")}


def processar_webhook_whatsapp(payload: dict) -> dict:
    """Processa webhook de mensagens recebidas no WhatsApp.

    Usado para:
    - Responder automaticamente a "status" ou "pedido"
    - Receber confirmações de entrega
    - Coletar feedback
    """
    # Extrair dados da mensagem recebida
    message = payload.get("message", {})
    phone = message.get("from", "")
    text = message.get("text", "").lower().strip()

    log.info("whatsapp.webhook.recebido", phone=phone, text=text[:50])

    # Respostas automáticas
    if text in ("status", "pedido", "acompanhar"):
        return {
            "ok": True,
            "auto_resposta": True,
            "mensagem": "Para verificar o status do seu pedido, acesse: " + BASE_URL + "/dashboard",
        }
    elif text in ("obrigado", "obg", "valeu"):
        return {
            "ok": True,
            "auto_resposta": True,
            "mensagem": "De nada! 😊 Se precisar de algo mais, é só chamar!",
        }
    elif text in ("ajuda", "help", "comandos"):
        return {
            "ok": True,
            "auto_resposta": True,
            "mensagem": (
                "📋 *Comandos disponíveis:*\n"
                "- *status* — Verificar status do pedido\n"
                "- *ajuda* — Ver esta mensagem\n"
                "- *sair* — Encerrar atendimento"
            ),
        }

    return {"ok": True, "auto_resposta": False, "text": text}
