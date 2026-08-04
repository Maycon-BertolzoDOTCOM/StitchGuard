"""Questionário para cadastro de máquina no catálogo.

O ateliê preenche as respostas, exporta um JSON, e o sistema valida antes de
adicionar ao catálogo de domain/maquinas.py.
"""

PERGUNTAS = [
    {"campo": "marca", "pergunta": "Marca da máquina", "tipo": "texto", "obrigatorio": True},
    {"campo": "modelo", "pergunta": "Modelo da máquina", "tipo": "texto", "obrigatorio": True},
    {"campo": "agulhas", "pergunta": "Número de agulhas", "tipo": "numero", "obrigatorio": True, "min": 1, "max": 20},
    {"campo": "formato_nativo", "pergunta": "Formato nativo", "tipo": "selecao", "obrigatorio": True,
     "opcoes": ["dst", "pes", "jef", "u01", "exp", "vp3", "pec"]},
    {"campo": "campo_largura", "pergunta": "Largura máxima do aro (mm)", "tipo": "numero", "obrigatorio": True, "min": 50, "max": 600},
    {"campo": "campo_altura", "pergunta": "Altura máxima do aro (mm)", "tipo": "numero", "obrigatorio": True, "min": 50, "max": 500},
    {"campo": "suporta_trim", "pergunta": "Tem cortador de linha?", "tipo": "booleano", "obrigatorio": True},
    {"campo": "max_ponto_mm", "pergunta": "Comprimento máximo do ponto (mm)", "tipo": "numero", "obrigatorio": False, "min": 1, "max": 20},
    {"campo": "max_salto_mm", "pergunta": "Comprimento máximo do salto (mm)", "tipo": "numero", "obrigatorio": False, "min": 1, "max": 20},
    {"campo": "comando_troca", "pergunta": "Comando para troca de cor", "tipo": "selecao", "obrigatorio": False,
     "opcoes": ["COLOR_CHANGE", "NEEDLE_SET"]},
    {"campo": "tipo", "pergunta": "Tipo de máquina", "tipo": "selecao", "obrigatorio": True,
     "opcoes": ["industrial", "domestica", "indefinido"]},
    {"campo": "observacoes", "pergunta": "Observações (opcional)", "tipo": "texto_longo", "obrigatorio": False},
]


def validar_respostas(respostas: dict) -> tuple:
    """Valida respostas do questionário.

    Returns:
        (bool, list[str]): (válido, lista de erros).
    """
    erros = []
    for p in PERGUNTAS:
        campo = p["campo"]
        if p.get("obrigatorio", False) and (campo not in respostas or respostas[campo] in (None, "")):
            erros.append(f"Campo obrigatório: {p['pergunta']}")
            continue
        if campo not in respostas or respostas[campo] in (None, ""):
            continue
        valor = respostas[campo]
        if p["tipo"] == "numero":
            try:
                v = float(valor)
                if p.get("min") is not None and v < p["min"]:
                    erros.append(f"{p['pergunta']}: mínimo {p['min']}")
                if p.get("max") is not None and v > p["max"]:
                    erros.append(f"{p['pergunta']}: máximo {p['max']}")
            except (TypeError, ValueError):
                erros.append(f"{p['pergunta']}: deve ser número")
        elif p["tipo"] == "selecao":
            if valor not in p.get("opcoes", []):
                erros.append(f"{p['pergunta']}: opção inválida. Opções: {', '.join(p.get('opcoes', []))}")
        elif p["tipo"] == "booleano" and valor not in [True, False]:
            erros.append(f"{p['pergunta']}: deve ser True ou False")
    return len(erros) == 0, erros


def gerar_template_json() -> dict:
    """Gera um template JSON com todas as perguntas (para o ateliê preencher)."""
    template = {}
    for p in PERGUNTAS:
        if p["tipo"] == "booleano":
            template[p["campo"]] = None
        elif p["tipo"] == "numero":
            template[p["campo"]] = None
        elif p["tipo"] == "selecao":
            template[p["campo"]] = p["opcoes"][0] if p.get("opcoes") else ""
        else:
            template[p["campo"]] = ""
    return template
