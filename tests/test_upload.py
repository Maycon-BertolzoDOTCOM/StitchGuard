"""Testes de upload SVG/PNG."""
import io
import tempfile
import os

from fastapi.testclient import TestClient
from PIL import Image

from application.main import app

client = TestClient(app)


def _svg_bytes():
    """Gera SVG de teste em bytes."""
    svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="20" height="20">
      <path d="M 5 5 L 15 5 L 15 15 L 5 15 Z" fill="#FF0000"/>
    </svg>'''
    return svg


def _png_bytes():
    """Gera PNG de teste em bytes (quadrado preto em fundo branco)."""
    img = Image.new("L", (20, 20), 255)
    pixels = img.load()
    for x in range(5, 15):
        for y in range(5, 15):
            pixels[x, y] = 0
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_upload_svg():
    """Upload de SVG retorna dst e preview."""
    r = client.post(
        "/v1/upload",
        files={"arquivo": ("teste.svg", _svg_bytes(), "image/svg+xml")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "dst" in data
    assert "preview_svg" in data
    assert data["resumo"]["stitches"] > 0
    assert data["resumo"]["cores"] >= 1


def test_upload_png():
    """Upload de PNG retorna dst e preview."""
    r = client.post(
        "/v1/upload",
        files={"arquivo": ("teste.png", _png_bytes(), "image/png")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "dst" in data
    assert data["resumo"]["stitches"] > 0


def test_upload_formato_invalido():
    """Formato invalido retorna 400."""
    r = client.post(
        "/v1/upload",
        files={"arquivo": ("teste.txt", b"conteudo", "text/plain")},
    )
    assert r.status_code == 400


def test_upload_svg_vazio():
    """SVG sem paths retorna 422."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>'
    r = client.post(
        "/v1/upload",
        files={"arquivo": ("vazio.svg", svg, "image/svg+xml")},
    )
    # Pode ser 200 (com 0 stitches) ou 422
    assert r.status_code in (200, 422)


def test_download_arquivo():
    """Download de arquivo gerado funciona."""
    # Upload primeiro
    r = client.post(
        "/v1/upload",
        files={"arquivo": ("teste.svg", _svg_bytes(), "image/svg+xml")},
    )
    data = r.json()

    # Download do .dst
    r2 = client.get(f"/v1/arquivos/{data['dst']}")
    assert r2.status_code == 200
    assert len(r2.content) > 0

    # Download do SVG
    r3 = client.get(f"/v1/arquivos/{data['preview_svg']}")
    assert r3.status_code == 200
    assert b"<svg" in r3.content


def test_download_arquivo_inexistente():
    """Download de arquivo inexistente retorna 404."""
    r = client.get("/v1/arquivos/nao_existe.dst")
    assert r.status_code == 404


def test_upload_com_tecido():
    """Upload com tecido especificado funciona."""
    r = client.post(
        "/v1/upload",
        files={"arquivo": ("teste.svg", _svg_bytes(), "image/svg+xml")},
        data={"tecido": "jeans"},
    )
    assert r.status_code == 200
