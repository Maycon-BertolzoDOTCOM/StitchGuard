# L6 — Infra (Fila + Persistência + Logging)

**Responsabilidade:** Gerenciamento de fila de jobs, persistência de dados, logs estruturados.

**MVP:** SQLite (fila + persistência) ✅
**Futuro:** Postgres + Redis

## Módulos

- `storage.py` — SQLAlchemy 2.0 (ORML) + modelos `Job` (fila) e `Validacao` (checklist 11 itens por job). `init_db()` cria as tabelas. URL via env `STITCHGUARD_DB_URL` (padrão `sqlite:///stitchguard.db`).
- `fila.py` — fila persistente em SQLite: `enfileirar()`, `obter_proximo()`, `obter_job()`, `atualizar_status()`. Estados: `pendente` → `processando` → `concluido`/`erro`. Idempotência: `calcular_hash()`, `obter_por_hash()` (TTL 24h). Validações: `salvar_validacoes()`, `obter_validacoes()`.
- `logger.py` — structlog configurado; utilizado em `application/main.py` e `infra/fila.py`.

## Integração com a API (L1)

`application/main.py` persiste cada job `POST /v1/pedido` via `fila.enfileirar()`,
processa em thread assíncrona (`_processar_job`) e o `GET /v1/pedido/{id}/status`
lê do banco — permitindo polling e rastreabilidade reais entre reinícios da API.

## Modelo Job (SQLAlchemy)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | str PK | `job_id` |
| `status` | str | pendente/processando/concluido/erro |
| `content_hash` | str(64) | SHA-256 para idempotência (index) |
| `arte` | text | JSON da arte (opcional) |
| `params` | text | parâmetros do pedido (tecido, máquina, ...) |
| `resultado` | text | JSON do resultado do pipeline |
| `erro` | text | mensagem de erro se falhou |
| `criado_em` / `atualizado_em` | str ISO | timestamps |

## Modelo Validacao (SQLAlchemy)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | int PK | autoincrement |
| `job_id` | str FK | referência ao Job |
| `item` | str(30) | nome do item do checklist (ex: "compensacao", "densidade") |
| `score` | float nullable | score fracionário (0.0–1.0 ou None) |
| `aprovado` | bool | se o item passou |
| `detalhe` | text nullable | descrição do resultado |
| `criado_em` | str ISO | timestamp |

## Testes

```bash
./venv/bin/python -m pytest tests/ -q
```