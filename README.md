# StitchGuard 🧵

**Sistema de automação para programação de matrizes de bordado**

Pipeline completo: **Arte → Geração → Validação → Otimização → Entrega**

[![CI](https://github.com/Maycon-BertolzoDOTCOM/StitchGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/Maycon-BertolzoDOTCOM/StitchGuard/actions/workflows/ci.yml)

## Visão Geral

StitchGuard é um orquestrador autônomo de bordado que:
- Gera arquivos `.dst` a partir de imagens (SVG/PNG) via auto-digitize (OpenCV)
- Valida automaticamente com checklist de 11 itens
- Otimiza saltos e compensa pull/push
- Processa em batch (sync e async via ARQ)
- Dashboard visual para ateliês
- Notificações via WhatsApp (Evolution/Meta/Z-API)
- Entrega via Google Drive
- Fatura via Asaas (Pix/Boleto)

**Não é um concorrente do Wilcom** — é uma camada de orquestração que usa Wilcom como provider opcional.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      L1 - Application                       │
│                    FastAPI (40 endpoints)                    │
├─────────────────────────────────────────────────────────────┤
│  L2 Domain │ L3 Generation │ L4 Validation │ L5 Commercial │
│  Presets   │ cli_anything  │ Checklist 11  │ Asaas/Drive   │
│  Máquinas  │ Router        │ Metrics       │ Email/Notif   │
├─────────────────────────────────────────────────────────────┤
│                     L6 - Infrastructure                     │
│              SQLite/PostgreSQL • Fila • S3/MinIO            │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone
git clone https://github.com/Maycon-BertolzoDOTCOM/StitchGuard.git
cd StitchGuard

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -q

# Start API
uvicorn application.main:app --reload --port 8000
```

## Endpoints (40)

| Grupo | Endpoint | Descrição |
|-------|----------|-----------|
| **Core** | `GET /health` | Health check |
| | `GET /v1/maquinas` | Catálogo de máquinas |
| | `GET /v1/presets` | Presets de tecido |
| | `GET /v1/formatos` | Formatos de exportação |
| | `GET /v1/fontes` | Fontes de bordado |
| **Pedidos** | `POST /v1/pedido` | Criar job (gerar→validar→otimizar) |
| | `GET /v1/pedido/{id}/status` | Status do job |
| | `GET /v1/pedido/{id}/validacoes` | Checklist de validação |
| | `POST /v1/pedido/{id}/editar` | Pós-edição (7 operações) |
| | `POST /v1/pedido/{id}/exportar` | Exportar para PES/EXP/VP3/XXX |
| | `GET /v1/pedido/{id}/laudo` | Laudo técnico HTML |
| | `GET /v1/preview/{id}` | Preview SVG com cores |
| **Upload** | `POST /v1/upload` | Upload SVG/PNG/.dst (com validação) |
| | `GET /v1/artefatos/{id}` | Download .dst |
| **Lettering** | `POST /v1/lettering` | Texto → matriz de bordado |
| **Billing** | `GET /v1/billing/planos` | Planos (Bronze/Prata/Ouro) |
| | `POST /v1/billing/criar-cobranca` | Criar cobrança |
| **Feedback** | `POST /v1/pedido/{id}/aprovar` | Aprovar matriz |
| | `POST /v1/pedido/{id}/rejeitar` | Rejeitar com observações |
| **Notificações** | `POST /v1/notificar/enviar` | Enviar email |
| | `POST /v1/notificar/webhook-typeform` | Webhook Typeform |
| | `POST /v1/notificar/whatsapp` | Enviar WhatsApp |
| | `POST /v1/notificar/whatsapp-webhook` | Webhook WhatsApp |
| **Batch** | `POST /v1/batch` | Upload em lote (sync) |
| | `POST /v1/batch/async` | Upload em lote (async/ARQ) |
| | `GET /v1/batch/{id}/status` | Status do batch |
| **Dashboard** | `GET /v1/dashboard` | Dashboard JSON |
| | `GET /v1/dashboard/html` | Dashboard visual HTML |
| **Entrega** | `POST /v1/entrega/upload` | Upload para Drive |
| | `POST /v1/entrega/link` | Link de download |
| **Auth** | `POST /v1/auth/register` | Registro |
| | `POST /v1/auth/login` | Login JWT |

## Stack

- **Python 3.13** + **FastAPI**
- **SQLAlchemy 2.0** (SQLite dev / PostgreSQL prod)
- **pyembroidery** (geração .dst)
- **OpenCV** (auto-digitize de imagens)
- **ARQ + Redis** (processamento assíncrono)
- **Asaas** (billing Pix/Boleto)
- **Google Drive** (entrega)
- **WhatsApp** (Evolution API / Meta Cloud / Z-API)
- **Docker** (multi-stage build)

## Configuração

```bash
# .env.example
DATABASE_URL=sqlite:///stitchguard.db
JWT_SECRET_KEY=your-secret-key
ASAAS_API_KEY=your-asaas-key
GOOGLE_DRIVE_CREDENTIALS=path/to/credentials.json
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
REDIS_URL=redis://localhost:6379

# WhatsApp (stub = desenvolvimento)
WHATSAPP_PROVIDER=stub
WHATSAPP_API_URL=http://localhost:8080
WHATSAPP_API_TOKEN=
```

## Testes

```bash
# 199 testes
python -m pytest tests/ -v

# Com cobertura
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

## Deploy

```bash
# Docker Compose
docker-compose up -d

# Services:
# - api: FastAPI (port 8000)
# - worker: ARQ worker
# - redis: Queue backend
# - postgres: Database (prod)
# - minio: Object storage
```

## Documentação

- [Arquitetura](STITCHGUARD_LAYERS.md)
- [Blueprint](STITCHGUARD_BLUEPRINT.md)
- [Wilcom vs StitchGuard](docs/WILCOM_VS_STITCHGUARD.md)
- [Pendências](PENDENCIAS_EXTERNAS.md)
- [Convenções BR](PESQUISA_CONVENCOES_BR.md)

## License

Proprietary - Maycon Bertolzo
