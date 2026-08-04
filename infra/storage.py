"""Persistencia — SQLAlchemy (SQLite para dev, PostgreSQL para producao)."""
import os

from sqlalchemy import create_engine, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DB_URL = os.environ.get("STITCHGUARD_DB_URL", "sqlite:///stitchguard.db")

# SQLite precisa de check_same_thread; PostgreSQL nao
connect_args = {"check_same_thread": False} if "sqlite" in DB_URL else {}
engine = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    """Usuario da plataforma (auth JWT)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(nullable=False, default=False)
    criado_em: Mapped[str] = mapped_column(String(40), nullable=False)


class Job(Base):
    """Job da fila: estado do pipeline gerar -> validar -> otimizar."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pendente")
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    arte: Mapped[str | None] = mapped_column(Text, nullable=True)
    params: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    resultado: Mapped[str | None] = mapped_column(Text, nullable=True)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[str] = mapped_column(String(40), nullable=False)
    atualizado_em: Mapped[str] = mapped_column(String(40), nullable=False)


class Validacao(Base):
    """Resultado da validacao por item do checklist (11 por job)."""

    __tablename__ = "validacoes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(32), ForeignKey("jobs.id"), index=True)
    item: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[float | None] = mapped_column(nullable=True)
    aprovado: Mapped[bool] = mapped_column(nullable=False)
    detalhe: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[str] = mapped_column(String(40), nullable=False)


def init_db() -> None:
    """Cria as tabelas no banco (idempotente)."""
    Base.metadata.create_all(engine)
