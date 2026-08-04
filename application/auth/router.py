"""Auth — rotas register, login, refresh."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select

from application.auth.dependencies import get_current_user
from application.auth.models import User
from application.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from infra.storage import SessionLocal

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest):
    with SessionLocal() as session:
        existing = session.execute(
            select(User).where((User.email == payload.email) | (User.username == payload.username))
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="Email ou username ja cadastrado")

        from datetime import datetime, timezone
        user = User(
            email=payload.email,
            username=payload.username,
            hashed_password=get_password_hash(payload.password),
            full_name=payload.full_name,
            criado_em=datetime.now(timezone.utc).isoformat(),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    access_token = create_access_token(data={"user_id": user.id, "sub": user.email})
    refresh_token = create_refresh_token(data={"user_id": user.id, "sub": user.email})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    with SessionLocal() as session:
        user = session.execute(
            select(User).where(User.email == form_data.username)
        ).scalar_one_or_none()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Conta desativada")

    access_token = create_access_token(data={"user_id": user.id, "sub": user.email})
    refresh_token = create_refresh_token(data={"user_id": user.id, "sub": user.email})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest):
    decoded = decode_token(payload.refresh_token)
    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token invalido ou expirado")
    user_id = decoded.get("user_id")
    with SessionLocal() as session:
        user = session.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Usuario nao encontrado ou inativo")
    access_token = create_access_token(data={"user_id": user.id, "sub": user.email})
    refresh_token = create_refresh_token(data={"user_id": user.id, "sub": user.email})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
