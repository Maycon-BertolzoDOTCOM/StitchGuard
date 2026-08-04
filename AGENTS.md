# StitchGuard — Regras do Projeto

Sistema de automação para programação de matrizes de bordado (.dst/.pes).
Pipeline: receber arte → gerar (L3) → validar (L4) → otimizar → entregar (L5).

## Camadas

- L0 Interface: Forms/Tally (MVP) → React (futuro)
- L1 Application: FastAPI em `application/main.py` (porta uvicorn **8000**)
- L2 Domain: `domain/presets.py` (tecidos) + `domain/maquinas.py` (catálogo)
- L3 Generation: `generation/router.py` (ProviderRouter) + `cli_anything` (pyembroidery)
- L4 Validation: `validation/checklist.py` (11 itens)
- L5 Commercial: Asaas (stub) + Drive/SMTP (stub)
- L6 Infra: `infra/fila.py` + `infra/storage.py` (SQLite, SQLAlchemy)

## Regras de domínio (não negociáveis)

1. **Geração:** use o provedor `cli_anything` (pyembroidery, 1 unidade == 1 mm). NUNCA use Inkscape/InkStitch em produção (headless).
2. **Validação item 10 (cores):** conte cores via `metrics.pattern.get_as_colorblocks()` — não `thread_colors()`.
3. **Máquina:** itens 10 (agulhas) e 11 (aro) só são aplicados se `maquina_id` for informado; senão score=None e ficam fora da média.
4. **Otimizador:** é computado DENTRO de `run_checklist()` (checklist.py, `otimizacao_saltos`), não "antes" do checklist.
5. **Scores do checklist:** fracionários reais 0.0 / 0.2 / 0.3 / 0.5 / 1.0 / None. Não padronize para só 0/0.5/1 — isso mudaria a média.
6. **Cetim:** variantes ralo/padrao/denso (`--preset`). Valores a validar com ateliê (TODO em `domain/presets.py:76`).
7. **Limite de salto (item 5):** usa `min(preset.salto_max, maquina.max_salto_mm)`.

## Índice de documentação

- Arquitetura detalhada: `STITCHGUARD_LAYERS.md`
- Pendências externas (credenciais, ateliê): `PENDENCIAS_EXTERNAS.md`
- Convenções do setor (densidade, tamanhos, preços): `PESQUISA_CONVENCOES_BR.md`
- Testes: `tests/test_api.py` via `./venv/bin/python -m pytest tests/ -q`

## Manutenção deste arquivo

- Adicione regra **somente se não for dedutível** pelo modelo (fatos do domínio ou restrições do projeto).
- Prefira apontar para a documentação em vez de copiar conteúdo.
- Remova regras genéricas de código (PEP 8, docstrings, boas práticas) — o modelo já sabe.
