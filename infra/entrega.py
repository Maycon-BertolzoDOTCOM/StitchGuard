"""Entrega — integração com Google Drive para uploads automáticos.

Endpoints:
- POST /v1/entrega/upload → upload de arquivo para Drive
- POST /v1/entrega/link → gera link de download

Dependências:
- Google Drive OAuth configurado via variáveis de ambiente
"""
import os
from datetime import datetime, timezone

import structlog

log = structlog.get_logger()

# Configuração Google Drive
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
GOOGLE_DRIVE_CREDENTIALS = os.environ.get("GOOGLE_DRIVE_CREDENTIALS", "")

# URL base para links de download
BASE_URL = os.environ.get("BASE_URL", "https://stitchguard.com.br")


def upload_para_drive(
    arquivo_path: str,
    nome_cliente: str,
    job_id: str,
) -> dict:
    """Faz upload de arquivo para Google Drive.

    Args:
        arquivo_path: caminho do arquivo local
        nome_cliente: nome do cliente (para organização)
        job_id: ID do job

    Returns:
        dict com file_id e download_url
    """
    if not GOOGLE_DRIVE_CREDENTIALS:
        # Modo stub (desenvolvimento)
        log.warning("drive.stub", arquivo=arquivo_path, job_id=job_id)
        return {
            "ok": True,
            "stub": True,
            "file_id": f"stub_{job_id}",
            "download_url": f"{BASE_URL}/v1/artefatos/{job_id}",
        }

    # Upload real via Google Drive API
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        # Autenticar
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_DRIVE_CREDENTIALS,
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
        service = build("drive", "v3", credentials=credentials)

        # Criar pasta do cliente (se não existir)
        folder_id = _criar_pasta_cliente(service, nome_cliente)

        # Upload do arquivo
        file_metadata = {
            "name": os.path.basename(arquivo_path),
            "parents": [folder_id],
        }
        media = MediaFileUpload(arquivo_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
        ).execute()

        file_id = file.get("id")

        # Gerar link de download
        download_url = f"https://drive.google.com/uc?id={file_id}"

        log.info("drive.upload", file_id=file_id, job_id=job_id)

        return {
            "ok": True,
            "stub": False,
            "file_id": file_id,
            "download_url": download_url,
        }
    except Exception as e:
        log.error("drive.erro", erro=str(e), job_id=job_id)
        return {"ok": False, "error": str(e)}


def _criar_pasta_cliente(service, nome_cliente: str) -> str:
    """Cria pasta para o cliente no Drive (se não existir)."""
    # Buscar pasta existente
    query = f"name='{nome_cliente}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    # Criar nova pasta
    file_metadata = {
        "name": nome_cliente,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if GOOGLE_DRIVE_FOLDER_ID:
        file_metadata["parents"] = [GOOGLE_DRIVE_FOLDER_ID]

    file = service.files().create(body=file_metadata, fields="id").execute()
    return file.get("id")


def gerar_link_download(
    job_id: str,
    expiracao_horas: int = 24,
) -> dict:
    """Gera link de download temporário.

    Args:
        job_id: ID do job
        expiracao_horas: tempo de expiração em horas

    Returns:
        dict com download_url e expiração
    """
    from datetime import timedelta

    download_url = f"{BASE_URL}/v1/artefatos/{job_id}"

    expiracao = datetime.now(timezone.utc) + timedelta(hours=expiracao_horas)

    return {
        "ok": True,
        "download_url": download_url,
        "expira_em": expiracao.isoformat(),
        "expiracao_horas": expiracao_horas,
    }


def listar_arquivos_cliente(nome_cliente: str) -> dict:
    """Lista arquivos de um cliente no Drive.

    Args:
        nome_cliente: nome do cliente

    Returns:
        dict com lista de arquivos
    """
    if not GOOGLE_DRIVE_CREDENTIALS:
        return {
            "ok": True,
            "stub": True,
            "arquivos": [],
        }

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_DRIVE_CREDENTIALS,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
        service = build("drive", "v3", credentials=credentials)

        # Buscar pasta do cliente
        query = f"name='{nome_cliente}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id)").execute()
        folders = results.get("files", [])

        if not folders:
            return {"ok": True, "arquivos": []}

        folder_id = folders[0]["id"]

        # Listar arquivos na pasta
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType, size, createdTime)",
        ).execute()

        arquivos = results.get("files", [])

        return {"ok": True, "arquivos": arquivos}
    except Exception as e:
        log.error("drive.listar_erro", erro=str(e))
        return {"ok": False, "error": str(e)}
