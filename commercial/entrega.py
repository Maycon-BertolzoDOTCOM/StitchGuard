"""Entrega do arquivo final via Google Drive + e-mail."""


def entregar(job_id: str, arquivo_path: str, cliente_email: str) -> dict:
    """Faz upload para o Drive, gera link publico e envia e-mail.

    Retorna {"link": ..., "status": "entregue"}.
    """
    raise NotImplementedError("Integracao com Drive/SMTP pendente.")
