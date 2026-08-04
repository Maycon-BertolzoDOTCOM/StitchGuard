# StitchGuard — Arquitetura em Camadas

## Mapa de Camadas

| Camada | Responsabilidade | Arquivos principais | Ferramentas |
|--------|------------------|---------------------|-------------|
| **L0 — Interface** | Recepção de pedidos (upload de arte + tecido + parâmetros) | `interface/` (futuro frontend) | Tally/Google Forms (MVP), React+Vite (futuro) |
| **L1 — Application** | Rotas HTTP + middleware (auth, rate-limit, idempotência) | `application/main.py` (FastAPI) | FastAPI, Uvicorn, Pydantic |
| **L2 — Domain** | Entidades de negócio (Pedido, Cliente, Matriz, Validacao) | `domain/` (dataclasses/Pydantic) | Python puro, Pydantic v2 |
| **L3 — Generation** | ProviderRouter: cascata de provedores (Ink/Stitch → Wilcom → humano) | `generation/router.py`, `generation/providers/*.py` | Ink/Stitch CLI, cli-anything-inkstitch, Wilcom APIs, asyncio |
| **L4 — Validation** | Validação da matriz (checklist de 11 itens, score) | `validation/` | pyembroidery, libembroidery |
| **L5 — Commercial** | Cobrança (Asaas) + entrega (Google Drive) + notificações (e-mail) | `commercial/asaas.py`, `commercial/entrega.py` | Asaas API, Google Drive API, SMTP |
| **L6 — Infra** | Fila (SQLite → Redis), persistência (SQLite → Postgres), logging | `infra/fila.py`, `infra/storage.py`, `infra/logger.py` | SQLite, SQLAlchemy, structlog |

## Diagrama de Fluxo

```mermaid
flowchart TD
    A[Cliente] --> B[L0: Interface<br/>Google Forms/Tally]
    B --> C[L1: Application<br/>FastAPI + Middleware]
    C --> D[L2: Domain<br/>Pedido, Cliente, Matriz]
    D --> E[L3: Generation<br/>ProviderRouter]
    E --> F[L3a: Ink/Stitch CLI (cost 0)]
    E --> G[L3b: cli-anything-inkstitch (cost 0)]
    E --> H[L3c: Wilcom APIs (cost 1)]
    E --> I[L3d: Digitador Humano (fallback)]
    F & G & H & I --> J[L4: Validation<br/>Checklist 11 itens<br/>pyembroidery]
    J --> K{Score >= 0.85?}
    K -->|Sim| L[L5: Commercial<br/>Asaas + Drive + E-mail]
    K -->|Nao| M[Notificar humano<br/>correção manual]
    L --> N[L6: Infra<br/>SQLite → Postgres<br/>Fila: Trello → Redis]
```

## Decisões Técnicas

- **Backend:** Python + FastAPI (validador já em Python; integração com Ink/Stitch mais direta; OpenAPI automático para polling JobId)
- **Persistência:** SQLite no MVP, migração para Postgres quando escalar
- **Fila:** Trello via API no MVP, substituir por Redis quando houver volume
- **Interface:** Tally/Google Forms para MVP, React+Vite no futuro
- **Provedores:** cascata por costTier com fallback humano — inspirado no ProviderRouter do MaterialView-Pro
- **Roteamento por dificuldade:** tarefas `high` pulam provedores gratuitos (DifficultyEstimator)
- **Validação:** checklist de 11 itens com pontuação contínua (0–1), threshold 0.85

## Dependências entre Camadas

- L0 → L1: formulário envia dados para API
- L1 → L2: API utiliza entidades de domínio
- L2 → L3: Pedido é roteado para provedor
- L3 → L4: matriz gerada passa pelo validador
- L4 → L5: se aprovado, comercializa e entrega
- L5 → L6: persiste status e logs

## Ferramentas Open-Source por Camada

| Camada | Ferramenta | Licença | Para quê |
|--------|------------|---------|----------|
| L3 | Ink/Stitch | GPLv3 | Gerar matriz (digitização completa) |
| L3 | cli-anything-inkstitch | Apache-2.0 | Automação stateful do Ink/Stitch (params/validate/fix) |
| L4 | pyembroidery | MIT | Ler/validar 46 formatos (base do validador) |
| L4 | libembroidery | LGPL | CLI `embroider` (conversão batch/medições) |
| L6 | SQLite | Public Domain | Persistência MVP |
| L6 | SQLAlchemy | MIT | ORM |
| L1 | FastAPI | MIT | API assíncrona + OpenAPI |
| L1 | Uvicorn | BSD | Servidor ASGI |

## Preset Cetim com Dial Rotativo

O tecido `cetim` (fonte única em `domain/presets.py`) possui três variantes de
densidade, acessíveis via flag `--preset`:

| Variante | Densidade (mm/ponto) | Underlay | Compensação | Uso |
|----------|----------------------|----------|-------------|-----|
| `ralo` | (0.45, 0.60) | não | media | Cetim fino, evita rasgar |
| `padrao` | (0.40, 0.55) | não | media | Cetim padrão (default) |
| `denso` | (0.35, 0.50) | não | media | Cetim grosso, pontos mais fechados |

```bash
./venv/bin/python -m validation.cli matriz.dst --tecido cetim --preset ralo --compensacao media
./venv/bin/python -m validation.cli matriz.dst --tecido cetim --preset denso --compensacao media
```

O detalhe de cada item reporta qual variante foi usada. O valor definitivo deve ser
validado com um ateliê real (`TODO validar com atelie` em `domain/presets.py`).

## L1 — API FastAPI (Application)

A camada L1 expõe o pipeline como serviço: catálogo, validação e jobs
(gerar → validar → otimizar) com polling e download do `.dst`.

```bash
./venv/bin/uvicorn application.main:app --reload --port 8000   # docs em /docs
curl -X POST localhost:8000/v1/pedido -H "Content-Type: application/json" -d '{"tecido":"jeans"}'
```

| Endpoint | Função |
|----------|--------|
| `GET /health` | Health check |
| `GET /v1/maquinas` / `GET /v1/presets` | Catálogo e presets |
| `POST /v1/validar` | Valida `.dst` enviado (multipart) |
| `POST /v1/pedido` (202 + jobId) → `GET /v1/pedido/{id}/status` | Job gerar→validar→otimizar com polling |
| `GET /v1/artefatos/{id}` | Download do `.dst` |
| `POST /v1/billing/webhook` | Stub Asaas (501) |

Jobs são persistidos em SQLite (`infra/fila.py`) e processados em thread assíncrona —
o polling lê do banco, sobrevivendo a reinícios da API.

## L6 — Fila e Persistência (Infra)

`infra/fila.py` + `infra/storage.py` (SQLAlchemy 2.0) implementam a fila de jobs em
SQLite: `enfileirar`/`obter_job`/`atualizar_status` com estados
`pendente → processando → concluido/erro`. A API (L1) conecta `POST /v1/pedido` à fila
e o status/polling lê do banco (`STITCHGUARD_DB_URL`, padrão `sqlite:///stitchguard.db`).

```bash
./venv/bin/python -m pytest tests/ -q   # regressão da API (L1+L6)
```

## Otimizador de Sequência (greedy TSP)

`generation/otimizador.py` implementa o algoritmo do vizinho mais próximo para
reordenar objetos e minimizar saltos (conecta ao item 5 do checklist).

```python
from generation.otimizador import relatorio_otimizacao
print(relatorio_otimizacao([(0, 0), (10, 0), (0, 10)]))
```

O relatório mostra a redução total e percentual dos saltos antes/depois.

**Integração com o checklist (L4):** `run_checklist()` agora extrai os centros
dos blocos de cor via `metrics.blocos_centros()` e inclui `otimizacao_saltos`
no resultado — exibido no CLI como:

```
OTIMIZACAO: saltos totais 3828.43mm -> 3000.0mm (melhoria 21.6%)
```

## Geração Funcional (L3 → L4 end-to-end)

O ProviderRouter **não é mais esqueleto**: o provedor `cli-anything` (cost 0)
gera `.dst` reais via pyembroidery a partir do JSON de arte, fechando o ciclo
gerar → validar → otimizar sem depender de Inkscape/InkStitch.

```bash
./venv/bin/python -m generation.cli arte.json \
    --tecido jeans --compensacao media [--preset ralo|padrao|denso] [--underlay]
```

- `generation/rascunho.py`: núcleo de digitalização (`rastrear_bloco`) — lock
  stitch, underlay de contorno (running stitch + zig-zag p/ formas largas),
  fill em serpentina com passo = meio da faixa de densidade, compensação
  geométrica por preset.
- `generation/providers/cli_anything.py`: gera a matriz (convenção **1 unidade
  pyembroidery == 1 mm**).
- `generation/cli.py`: pipeline completo que roteia (L3), valida (L4) e reporta
  a otimização.

| Provedor | costTier | Status |
|----------|----------|--------|
| Ink/Stitch CLI | 0 | Hook pendente (exige Inkscape) |
| cli-anything (interno) | 0 | ✅ Funcional (geração via pyembroidery) |
| Wilcom APIs | 1 | Pendente (dificuldade `high` cai aqui) |
| Digitador Humano | 99 | Pendente |

**Limite conhecido:** blocos distantes em uma arte (ex.: cantos de 100x100mm)
reprovam o item 5 (saltos) **por design** — é o checklist funcionando. A amostra
padrão usa blocos compactos para demonstrar a otimização sem violar o limite.

**Detalhe de API:** o validador conta `pe.STOP` e `pe.COLOR_CHANGE` como paradas
(o DST reescreve STOP como COLOR_CHANGE na leitura), garantindo o item 8.

## Oportunidades do Vídeo de Cetim (Satin) — Status Real

Mapa do vídeo do professor Danilo → o que é **realmente** automatizável hoje:

| Etapa (manual ~83min) | Status de automação | Ferramenta |
|------------------------|---------------------|------------|
| Texto curvo (Linha de Ângulo) | ✅ Automatável via CLI | Ink/Stitch `--extension=batch_lettering --text=... --file-formats="dst,svg"` |
| Contornos (elipse → esteio) | ⚠️ Parcial | pyembroidery + detecção de formas |
| Silhueta em múltiplos objetos | ⚠️ Parcial (fase 3: OpenCV) | Ink/Stitch auto-fill/auto-satin + segmentação |
| Ângulos do satin | ❌ Manual (heurística futura) | — |
| Organização de sequência | ✅ Automatável | `generation/otimizador.py` (greedy TSP) |
| Configuração de pontos por tecido | ✅ Automatável | `domain/presets.py` (dial cetim) |
| Exportação PES/DST/PDF | ✅ Automatável | pyembroidery + ReportLab |

**Nota:** o ganho 83min → 3min é aspiracional. Texto curvo, presets e otimização de
sequência são automatizáveis agora; silhueta segmentada e ângulos exigem OpenCV
(fase 3 do roadmap).

## Máquinas de Bordado (L2 + L4)

`domain/maquinas.py` gerencia o catálogo de máquinas. Cada máquina tem:
- `agulhas`: número de agulhas
- `formato_nativo`: dst/pes/jef/u01/exp/vp3/pec
- `campo_largura`/`campo_altura`: aro máximo em mm
- `suporta_trim`: True/False
- `max_ponto_mm`: comprimento máximo do ponto
- `max_salto_mm`: comprimento máximo do salto
- `comando_troca`: COLOR_CHANGE ou NEEDLE_SET
- `tipo`: industrial/domestica/indefinido

**Fallback:** `generica` (6 agulhas, dst, aro 300x300, trim True, max_ponto 12.1, max_salto 12.1).

**Questionário:** o ateliê preenche `domain/questionario_maquina.py`
(`PERGUNTAS`, `validar_respostas()`, `gerar_template_json()`) para cadastrar a
máquina real no catálogo.

**Novos itens no checklist (10 e 11) + ajustes:**
- **Item 10:** Número de cores ≤ agulhas da máquina (`get_as_colorblocks()`)
- **Item 11:** Matriz cabe no aro da máquina (largura/altura ≤ campo)
- **Item 5 (ajuste):** Limite de salto = `min(preset.salto_max, maquina.max_salto_mm)`
- **Item 8 (ajuste):** Se `suporta_trim=False`, avisa sobre nós extras após saltos
- Sem máquina informada → itens 10/11 com `score=None` (fora da média, regressão zero)

**Uso no CLI:**
```bash
./venv/bin/python -m validation.cli matriz.dst --tecido cetim --preset ralo --maquina tajima-tfmx-6
./venv/bin/python -m generation.cli arte.json --tecido jeans --maquina brother-pr1050x
```

**Formato de exportação:** definido pelo `formato_nativo` da máquina (geração futura).
