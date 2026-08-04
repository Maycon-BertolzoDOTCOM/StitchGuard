# L2 — Domain (Entidades de Negócio)

**Responsabilidade:** Definição das entidades centrais com validação de domínio.

**Stack:** Python puro (dataclasses → Pydantic v2)

**Entidades:**
- `Pedido` (Job): id, cliente_id, arte_url, tecido, maquina_id, status, timestamps
- `Cliente`: id, nome, email, plano
- `Matriz`: job_id, arquivo_url, pontos, formatos (PES/DST/JEF)
- `Validacao`: job_id, checklist (11 itens), score, aprovado

**Regras de negócio:**
- Status: Recebido → Processando → Validando → Concluído
- Score < 0.85 → rejeita e notifica humano

## Módulos

| Arquivo | Responsabilidade |
|---|---|
| `presets.py` | Tabela de tecidos + dial cetim (ralo/padrao/denso) |
| `maquinas.py` | Catálogo de máquinas + `get_maquina()` + fallback genérica |
| `questionario_maquina.py` | Perguntas e validador para cadastro de máquina |

## Uso

```python
from domain.presets import get_preset
from domain.maquinas import get_maquina

preset = get_preset("cetim", "ralo")
maquina = get_maquina("brother-pr1050x")  # fallback 'generica' se desconhecida
```
