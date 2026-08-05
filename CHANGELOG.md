# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.1.0] - 2026-08-04

### Added
- **Batch Processing**: upload em lote de múltiplos arquivos
  - `POST /v1/batch` — processamento síncrono
  - `POST /v1/batch/async` — processamento assíncrono via ARQ
  - `GET /v1/batch/{id}/status` — polling de status
- **Dashboard Visual**: interface HTML para ateliês
  - `GET /v1/dashboard` — dados JSON
  - `GET /v1/dashboard/html` — página HTML completa
- **WhatsApp Integration**: notificações via WhatsApp
  - `infra/whatsapp.py` — suporte Evolution API, Meta Cloud, Z-API
  - `POST /v1/notificar/whatsapp` — enviar mensagem
  - `POST /v1/notificar/whatsapp-webhook` — receber mensagens
- **Auto-digitize melhorado**: OpenCV + raster serpentine
  - Lock stitches (STOP) no início/fim de cada contorno
  - TRIM/JUMP entre contornos
  - Preenchimento raster serpentine (reduz saltos)
  - Raster fill scoring improved: 0.5 → 0.8

### Fixed
- `validation/metrics.py`: jumps() exclui TRIM/COLOR_CHANGE (corte de thread, não salto)
- Export .pes/.exp/.vp3 funcionando corretamente

### Changed
- Total de endpoints: 28 → 40
- Total de testes: 176 → 199
- `ruff.toml`: configuração limpa (regras UP removidas)

## [1.0.0] - 2026-08-04

### Added
- **L1 Application**: 28 endpoints FastAPI
  - Auth: register, login, refresh (JWT)
  - Pedidos: criar, status, validações, edição, laudo
  - Upload/Download: SVG/PNG → .dst
  - Billing: planos, criar cobrança, status, webhook (Asaas)
  - Feedback: aprovar, rejeitar
  - Notificações: enviar email, webhook Typeform
  - Entrega: upload Drive, link temporário, listar arquivos

- **L2 Domain**: Regras de negócio
  - 5 presets de tecido (malha, jeans, nylon, bone, cetim)
  - 10 máquinas reais + genérica
  - Catálogo completo com especificações

- **L3 Generation**: Geração de .dst
  - cli_anything (pyembroidery) como provider padrão
  - Router com DifficultyEstimator
  - image_processor para SVG/PNG → EmbPattern

- **L4 Validation**: Checklist automático
  - 11 itens de validação
  - Score global mínimo: 0.85
  - StitchMetrics para análise

- **L5 Commercial**: Billing e entrega
  - Integração Asaas (Pix/Boleto)
  - 4 planos: Bronze, Prata, Ouro, Avulso
  - Laudo técnico HTML
  - Feedback do cliente

- **L6 Infrastructure**: Storage e fila
  - SQLite (dev) / PostgreSQL (prod)
  - Fila com idempotência
  - S3/MinIO para armazenamento
  - Google Drive para entrega
  - Notificações por email
  - Webhook Typeform

- **Post-Editor**: 7 operações
  - Compensação pull
  - Ajustar densidade
  - Reordenar blocos
  - Inserir/remover pontos
  - Adicionar/remover underlay

- **Scripts**
  - Monitor de pasta (INPUT/OUTPUT)
  - Download de dataset
  - Processamento para classificador

- **Testes**: 176 testes unitários e de integração

- **Docker**: Multi-stage build + docker-compose

- **CI/CD**: GitHub Actions

### Changed
- N/A (primeira versão)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- JWT com expiração
- Senhas com bcrypt
- Variáveis sensíveis em .env
