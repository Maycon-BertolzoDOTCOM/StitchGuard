# L1 — Application (API + Middleware)

**Responsabilidade:** Rotas HTTP (pedidos, status, catálogo, billing, notificações, entrega) + middleware (auth, rate-limit, idempotência — futuro).

**Stack:** Python + FastAPI (já instalado no venv)

## Endpoints implementados (28 endpoints)

### Core
| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/v1/maquinas` | Catálogo de máquinas (`domain/maquinas.py`) |
| GET | `/v1/presets` | Presets de tecido (`domain/presets.py`) |

### Pedidos
| Método | Rota | Descrição |
|---|---|---|
| POST | `/v1/pedido` | Cria job gerar→validar→otimizar (202 + `job_id`) — L3→L4 |
| GET | `/v1/pedido/{job_id}/status` | Polling de status do job |
| GET | `/v1/pedido/{job_id}/validacoes` | Itens do checklist (11 por job) |
| POST | `/v1/pedido/{job_id}/editar` | Pós-edição avançada (7 operações) |
| GET | `/v1/pedido/{job_id}/laudo` | Gera laudo técnico HTML |
| GET | `/v1/pedido/{job_id}/laudo/html` | Retorna HTML do laudo diretamente |
| GET | `/v1/preview/{job_id}` | Preview SVG do bordado gerado |

### Upload/Download
| Método | Rota | Descrição |
|---|---|---|
| POST | `/v1/upload` | Upload SVG/PNG → gera .dst + preview |
| GET | `/v1/arquivos/{filename}` | Download de arquivo gerado (upload) |
| GET | `/v1/artefatos/{job_id}` | Download do `.dst` gerado |
| POST | `/v1/validar` | Valida um `.dst` enviado (multipart + form) — L4 |

### Billing
| Método | Rota | Descrição |
|---|---|---|
| GET | `/v1/billing/planos` | Lista planos (Bronze/Prata/Ouro/Avulso) |
| POST | `/v1/billing/criar-cobranca` | Cria cobrança Pix/Boleto |
| GET | `/v1/billing/status/{id}` | Verifica status do pagamento |
| POST | `/v1/billing/webhook` | Recebe notificação Asaas |

### Feedback
| Método | Rota | Descrição |
|---|---|---|
| POST | `/v1/pedido/{job_id}/aprovar` | Cliente aprova matriz |
| POST | `/v1/pedido/{job_id}/rejeitar` | Rejeita com observações |
| GET | `/v1/pedido/{job_id}/feedback` | Retorna feedback do cliente |

### Notificações
| Método | Rota | Descrição |
|---|---|---|
| POST | `/v1/notificar/enviar` | Envia e-mail de entrega |
| POST | `/v1/notificar/webhook-typeform` | Webhook do Typeform/Google Forms |

### Entrega
| Método | Rota | Descrição |
|---|---|---|
| POST | `/v1/entrega/upload` | Upload para Google Drive |
| POST | `/v1/entrega/link` | Gera link de download temporário |
| GET | `/v1/entrega/arquivos/{cliente}` | Lista arquivos do cliente |

### Auth
| Método | Rota | Descrição |
|---|---|---|
| POST | `/v1/auth/register` | Registro de usuário |
| POST | `/v1/auth/login` | Login JWT |
| POST | `/v1/auth/refresh` | Refresh token |
| Método | Rota | Descrição |
|---|---|---|
| POST | `/v1/auth/register` | Registro de usuário |
| POST | `/v1/auth/login` | Login JWT |
| POST | `/v1/auth/refresh` | Refresh token |

## Como rodar

```bash
./venv/bin/uvicorn application.main:app --reload --port 8000
```

Doc interativa em `http://localhost:8000/docs`.

## Exemplos

```bash
# Validar um .dst existente
curl -X POST http://localhost:8000/v1/validar \
  -F "arquivo=@/tmp/opencode/limpo.dst" \
  -F "tecido=nylon" -F "compensacao=media" -F "underlay=true" -F "maquina=generica"

# Gerar + validar com a amostra padrão
curl -X POST http://localhost:8000/v1/pedido \
  -H "Content-Type: application/json" \
  -d '{"tecido":"jeans","maquina":"tajima-tfmx-6"}'
# -> 202 {"job_id":"...","status":"concluido"}

# Polling + download
curl http://localhost:8000/v1/pedido/<job_id>/status
curl -OJ http://localhost:8000/v1/artefatos/<job_id>

# Preview SVG (abrir no navegador)
curl http://localhost:8000/v1/preview/<job_id> -o preview.svg

# Upload de SVG/PNG -> gera .dst + preview
curl -X POST http://localhost:8000/v1/upload \
  -F "arquivo=@logo.svg" -F "tecido=jeans"
# -> {"dst":"abc123.dst","preview_svg":"def456.svg","resumo":{...}}

# Download de arquivo gerado
curl -OJ http://localhost:8000/v1/arquivos/<filename>

# Pós-edição avançada (compensação + densidade)
curl -X POST http://localhost:8000/v1/pedido/<job_id>/editar \
  -H "Content-Type: application/json" \
  -d '{"operacoes":[{"tipo":"compensacao_pull","valor_mm":0.5},{"tipo":"ajustar_densidade","fator":0.9}]}'
# -> {"dst_editado":"...","preview_svg":"...","validacao":{...}}

# Gerar laudo técnico
curl http://localhost:8000/v1/pedido/<job_id>/laudo
# -> {"job_id":"...","laudo_html":"laudo_...html","score_global":0.91,"aprovado":true}
```

## Detalhes técnicos

- `arte` pode ser o JSON da arte como string no corpo do pedido (`None` => amostra padrão).
- Jobs são persistidos em SQLite via `infra/fila.py` (SQLAlchemy) e processados em thread
  assíncrona — o polling (`GET /v1/pedido/{id}/status`) lê do banco e sobrevive a reinícios.
  Estados: `pendente` → `processando` → `concluido`/`erro`.
- **Idempotência:** `POST /v1/pedido` deduplica via hash SHA-256 de (arte + params). Jobs idênticos dentro de 24h retornam o mesmo `job_id` com header `X-Idempotency: REPLAY`.
- **Logging:** structlog integrado em `application/main.py` e `infra/fila.py` (eventos: `pedido.criado`, `pedido.replay`, `job.inicio`, `job.concluido`, `job.erro`, `fila.enfileirar`, `fila.status`).
- Artefatos `.dst` ficam em um diretório temporário (`tempfile.mkdtemp`).
- Parâmetros: `tecido`, `preset`, `compensacao`, `underlay`, `maquina`, `dificuldade`.
- Migrações futuras: auth (API key), rate-limit, fila/persistência em Postgres/Redis.

**Dependências:** L2 (Domain), L3 (Generation), L4 (Validation), L6 (Infra — fila SQLite ✅).
