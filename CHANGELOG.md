# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

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
