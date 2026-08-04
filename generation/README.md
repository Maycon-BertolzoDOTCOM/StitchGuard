# L3 — Generation (ProviderRouter)

**Responsabilidade:** Roteamento do pedido para o provedor de geração de matriz mais adequado (cascade com cost tiers).

**Stack:** Python (subprocess, asyncio, pyembroidery)

**Provedores (em cascata):**
1. `Ink/Stitch CLI` (cost 0) — gera rascunho via auto-digitizing *(hook pendente)*
2. `cli-anything-inkstitch` (cost 0) — **provedor interno do MVP**: gera via pyembroidery a partir do JSON de arte
3. `Wilcom APIs` (cost 1) — se o rascunho for de baixa qualidade *(pendente)*
4. `Digitador Humano` (fallback) — nunca falha *(pendente)*

**Decisão de rota:** com base na complexidade estimada (número de cores, tamanho, curva).
Dificuldade `high` exige costTier >= 1 (pula os provedores locais).

## DifficultyEstimator (`difficulty.py`)

Computa dificuldade automaticamente a partir da arte e parâmetros (ou aceita string manual via `--dificuldade`):

| Fator | low | medium | high |
|-------|-----|--------|------|
| Tamanho (mm) | < 100 | 100–300 | > 300 |
| Nº de cores | ≤ 3 | 4–8 | > 8 |
| Nº de objetos | ≤ 8 | 9–20 | > 20 |
| Tecido | malha/nylon | jeans | boné |

Score ≥ 4 → `high`, ≥ 2 → `medium`, senão `low`.

```python
from generation.difficulty import estimar_dificuldade
d = estimar_dificuldade(arte, {"tecido": "bone"})  # "medium" ou "high"
```

## Provedor cli-anything (funcional)

Converte o JSON de arte (formas geométricas em mm) em `.dst` usando
`generation/rascunho.py` (núcleo de digitalização) e os presets de
`domain/presets.py`. Convenção: **1 unidade pyembroidery == 1 mm** neste pipeline.

## Processamento de imagens (`image_processor.py`)

Converte SVG/PNG para stitches (EmbPattern):

- **SVG:** parseia `<path>` com comandos M/L/H/V/C/S/Q/T/Z, converte para stitches
- **PNG:** extrai silhueta via edge detection (threshold + ordenação por proximidade)
- Curvas SVG são aproximadas com N segmentos lineares (default: 8)

```python
from generation.image_processor import processar_imagem
pattern = processar_imagem("logo.svg", tecido="jeans")
```

## Pipeline completo (L3 → L4)

```bash
./venv/bin/python -m generation.cli arte.json \
    --tecido jeans --compensacao media [--preset ralo|padrao|denso] [--underlay] \
    [--dificuldade low|medium|high] [--out saida.dst] [--json]
```

Gera a matriz via `router.route()`, valida com o checklist (L4) e imprime o
relatório final incluindo a otimização de saltos. Sem `arte.json`, usa uma
amostra padrão de 4 blocos (demonstra a otimização ~21%).

## JSON de arte (schema)

```json
{
  "nome": "Design de Teste",
  "largura_mm": 100.0,
  "altura_mm": 100.0,
  "objetos": [
    {"tipo": "retangulo", "x": 10.0, "y": 10.0, "largura": 80.0, "altura": 80.0, "cor": 0},
    {"tipo": "poligono", "pontos": [[20.0, 20.0], [80.0, 20.0], [50.0, 80.0]], "cor": 1},
    {"tipo": "circulo", "centro_x": 50.0, "centro_y": 50.0, "raio": 30.0, "cor": 2}
  ]
}
```

- `tipo`: `retangulo`, `poligono` ou `circulo`
- Coordenadas em **mm** (1 mm == 1 unidade pyembroidery)
- `cor`: índice da linha na paleta padrão
- `largura_mm`/`altura_mm`: metadados informativos

## Núcleo de digitalização (`rascunho.py`)

`rastrear_bloco(pattern, forma, preset)` aplica, por bloco:
1. Lock stitch inicial (3 pontinhos reversos)
2. Underlay de contorno (running stitch, passo 0.8mm, inset 1.0mm) + zig-zag central se largura > 15mm — quando `preset.underlay_exigido`
3. Preenchimento principal (fill em serpentina) com passo = meio da faixa de densidade do preset
4. Compensação geométrica conforme `preset.compensacao_exigida` (alta 0.8 / media 0.5 / baixa 0.3 mm)

### Testes (Etapa 4)

| Caso | Resultado |
|------|-----------|
| Amostra 4 blocos (jeans) | APROVADO score 1.0, otimização 21.7% |
| Retângulo+polígono+círculo (nylon, underlay) | APROVADO score 0.89 |
| Dial cetim ralo | APROVADO, passo 0.55mm (5439 pts) |
| Dial cetim denso | APROVADO, passo 0.43mm (8594 pts) |
| Dificuldade `high` | ERRO claro (wilcom não implementado) |

> **Atenção:** blocos distantes em arte (ex.: cantos de 100x100mm) reprovam
> o item 5 (saltos) por design — é o checklist funcionando. A amostra padrão
> usa blocos compactos para demonstrar a otimização sem violar o limite.
