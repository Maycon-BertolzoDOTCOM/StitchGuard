# L4 — Validation (Validador)

**Responsabilidade:** Verificação da matriz gerada pelo checklist de 11 itens (gerador-verificador).

**Stack:** Python + pyembroidery

**Módulos:**
- `metrics.py` — extrai métricas de .DST/.PES: dimensões, pontos, saltos, passo médio, paradas
- `checklist.py` — os 11 itens como scores contínuos [0–1], parametrizados por tecido
- `cli.py` — `python -m validation.cli matriz.dst --tecido nylon --compensacao media --underlay`

**Presets:** a tabela de tecidos vive em `domain/presets.py` (fonte única, compartilhada com geração L3).
O tecido `cetim` tem um dial de densidade: `--preset ralo|padrao|denso` (default `padrao`).

```bash
./venv/bin/python -m validation.cli matriz.dst --tecido cetim --preset ralo --compensacao media
./venv/bin/python -m validation.cli matriz.dst --tecido cetim --preset denso --compensacao media
```

**Threshold:** score global >= 0.85 aprova para entrega. Itens que exigem olho humano
(ordem de costura, ângulos do satin) ficam em `itens_pendentes_revisao_humana`.
