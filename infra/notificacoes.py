"""Notificações — e-mail automático na entrega de matrizes.

Endpoints:
- POST /v1/notificar/enviar → envia e-mail de entrega
- POST /v1/notificar/webhook-typeform → recebe webhook do Typeform/Google Forms

Dependências:
- SMTP configurado via variáveis de ambiente
"""
import os
from datetime import datetime, timezone

import structlog

log = structlog.get_logger()

# Configuração SMTP
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "stitchguard@exemplo.com")

# URL base para links de download
BASE_URL = os.environ.get("BASE_URL", "https://stitchguard.com.br")


def enviar_email_entrega(
    destinatario: str,
    nome_cliente: str,
    job_id: str,
    download_url: str,
    valor: float | None = None,
    plano: str | None = None,
) -> dict:
    """Envia e-mail de entrega da matriz.

    Args:
        destinatario: e-mail do cliente
        nome_cliente: nome do cliente
        job_id: ID do job
        download_url: link de download do .dst
        valor: valor cobrado (opcional)
        plano: plano contratado (opcional)

    Returns:
        dict com status do envio
    """
    assunto = f"StitchGuard - Sua matriz {job_id} está pronta!"

    corpo = f"""Olá {nome_cliente}!

Sua matriz de bordado foi processada com sucesso.

📦 **Detalhes do Pedido:**
- Job ID: {job_id}
- Data: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}

📥 **Download:**
Acesse o link abaixo para baixar seu arquivo .DST:
{download_url}

{f'💰 **Plano:** {plano}' if plano else ''}
{f'💵 **Valor:** R$ {valor:.2f}' if valor else ''}

---
StitchGuard - A Fábrica de Matrizes Autônoma
https://stitchguard.com.br
"""

    # Modo stub (desenvolvimento)
    if not SMTP_USER:
        log.warning("email.stub", destinatario=destinatario, job_id=job_id)
        return {
            "ok": True,
            "stub": True,
            "destinatario": destinatario,
            "assunto": assunto,
        }

    # Envio real via SMTP
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        log.info("email.enviado", destinatario=destinatario, job_id=job_id)

        return {
            "ok": True,
            "stub": False,
            "destinatario": destinatario,
        }
    except Exception as e:
        log.error("email.erro", erro=str(e), destinatario=destinatario)
        return {"ok": False, "error": str(e)}


def processar_webhook_typeform(payload: dict) -> dict:
    """Processa webhook do Typeform/Google Forms.

    Extrai dados do formulário e cria pedido automaticamente.

    Formato esperado do Typeform:
    {
        "form_id": "...",
        "answers": [
            {"field": {"ref": "nome"}, "text": "João"},
            {"field": {"ref": "email"}, "email": "joao@test.com"},
            {"field": {"ref": "whatsapp"}, "text": "+5511999999999"},
            {"field": {"ref": "arte"}, "file_url": "..."},
            {"field": {"ref": "tecido"}, "choice": {"label": "Jeans"}},
            {"field": {"ref": "prazo"}, "choice": {"label": "Normal (24h)"}},
        ]
    }
    """
    # Extrair respostas
    answers = payload.get("answers", [])

    dados = {}
    for answer in answers:
        field_ref = answer.get("field", {}).get("ref", "")
        if "text" in answer:
            dados[field_ref] = answer["text"]
        elif "email" in answer:
            dados[field_ref] = answer["email"]
        elif "file_url" in answer:
            dados[field_ref] = answer["file_url"]
        elif "choice" in answer:
            dados[field_ref] = answer["choice"].get("label", "")

    log.info("typeform.recebido", dados=dados)

    return {
        "ok": True,
        "nome": dados.get("nome", ""),
        "email": dados.get("email", ""),
        "whatsapp": dados.get("whatsapp", ""),
        "arte_url": dados.get("arte", ""),
        "tecido": dados.get("tecido", "generico"),
        "prazo": dados.get("prazo", "Normal (24h)"),
    }


def criar_pedido_de_webhook(dados: dict) -> dict:
    """Cria pedido a partir de dados do webhook.

    Args:
        dados: dict com nome, email, whatsapp, arte_url, tecido, prazo

    Returns:
        dict com job_id criado
    """
    from infra import fila
    import uuid

    job_id = uuid.uuid4().hex[:12]

    params = {
        "tecido": dados.get("tecido", "generico"),
        "cliente_nome": dados.get("nome", ""),
        "cliente_email": dados.get("email", ""),
        "cliente_whatsapp": dados.get("whatsapp", ""),
        "prazo": dados.get("prazo", "Normal (24h)"),
    }

    content_hash = fila.calcular_hash(dados.get("arte_url"), params)
    fila.enfileirar(job_id, dados.get("arte_url"), params, content_hash=content_hash)

    log.info("pedido.criado_webhook", job_id=job_id, cliente=dados.get("nome"))

    return {
        "ok": True,
        "job_id": job_id,
        "status": "pendente",
    }
