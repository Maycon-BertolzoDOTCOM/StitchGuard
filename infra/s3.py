"""Armazenamento S3 — boto3 (compativel com AWS S3 e MinIO)."""
import os
from urllib.parse import urlparse

import boto3
from botocore.config import Config
import structlog

log = structlog.get_logger()


def get_s3_client():
    endpoint = os.environ.get("S3_ENDPOINT")
    access_key = os.environ.get("S3_ACCESS_KEY", "")
    secret_key = os.environ.get("S3_SECRET_KEY", "")

    use_ssl = True
    if endpoint:
        parsed = urlparse(endpoint)
        use_ssl = parsed.scheme == "https"
        endpoint = endpoint.rstrip("/")

    return boto3.client(
        "s3",
        endpoint_url=endpoint or None,
        aws_access_key_id=access_key or None,
        aws_secret_access_key=secret_key or None,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 3, "mode": "standard"},
        ),
        use_ssl=use_ssl,
    )


def get_bucket_name() -> str:
    return os.environ.get("S3_BUCKET", "stitchguard")


async def upload_artefato(file_content: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    client = get_s3_client()
    bucket = get_bucket_name()
    client.put_object(Bucket=bucket, Key=key, Body=file_content, ContentType=content_type)
    log.info("s3.upload", bucket=bucket, key=key, size=len(file_content))
    return key


def generate_presigned_download(key: str, expires_in: int = 3600) -> str:
    client = get_s3_client()
    bucket = get_bucket_name()
    return client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def generate_presigned_upload(key: str, content_type: str, expires_in: int = 3600) -> str:
    client = get_s3_client()
    bucket = get_bucket_name()
    return client.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=expires_in,
    )


def delete_artefato(key: str) -> None:
    client = get_s3_client()
    bucket = get_bucket_name()
    client.delete_object(Bucket=bucket, Key=key)
    log.info("s3.delete", bucket=bucket, key=key)
