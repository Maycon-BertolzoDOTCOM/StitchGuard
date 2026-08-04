"""Testes de autenticacao JWT."""
import uuid

from fastapi.testclient import TestClient

from application.main import app

client = TestClient(app)


def _unique_email(prefix: str = "test") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@test.com"


def test_register():
    """Registro de novo usuario retorna tokens."""
    r = client.post("/v1/auth/register", json={
        "email": _unique_email("register"),
        "username": f"user_{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicado():
    """Email duplicado retorna 409."""
    email = _unique_email("dup")
    client.post("/v1/auth/register", json={
        "email": email,
        "username": f"dup1_{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    r = client.post("/v1/auth/register", json={
        "email": email,
        "username": f"dup2_{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    assert r.status_code == 409


def test_login():
    """Login retorna tokens."""
    email = _unique_email("login")
    client.post("/v1/auth/register", json={
        "email": email,
        "username": f"login_{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    r = client.post("/v1/auth/login", data={
        "username": email,
        "password": "senha123",
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_senha_errada():
    """Senha errada retorna 401."""
    email = _unique_email("err")
    client.post("/v1/auth/register", json={
        "email": email,
        "username": f"err_{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    r = client.post("/v1/auth/login", data={
        "username": email,
        "password": "errada",
    })
    assert r.status_code == 401


def test_refresh():
    """Refresh token retorna novos tokens."""
    r = client.post("/v1/auth/register", json={
        "email": _unique_email("refresh"),
        "username": f"refresh_{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    refresh_token = r.json()["refresh_token"]
    r2 = client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


def test_refresh_invalido():
    """Refresh token invalido retorna 401."""
    r = client.post("/v1/auth/refresh", json={"refresh_token": "invalido"})
    assert r.status_code == 401


def test_endpoint_protegido_sem_token():
    """Endpoint protegido sem token retorna 401."""
    r = client.post("/v1/pedido", json={"tecido": "jeans"})
    assert r.status_code == 401


def test_endpoint_protegido_com_token():
    """Endpoint protegido com token valido funciona."""
    r = client.post("/v1/auth/register", json={
        "email": _unique_email("auth"),
        "username": f"auth_{uuid.uuid4().hex[:6]}",
        "password": "senha123",
    })
    token = r.json()["access_token"]
    r2 = client.post("/v1/pedido",
        json={"tecido": "jeans"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 202
