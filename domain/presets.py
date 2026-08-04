"""Tabela de presets por tecido — fonte unica de verdade para geracao (L3) e validacao (L4)."""

DENSIDADE_DEFAULT = (0.35, 0.50)
SALTO_DEFAULT_MM = 5.0

# Estrutura por tecido:
#   compensacao_exigida: "alta" | "media" | "baixa" | None (sem regra)
#   underlay_exigido:    bool | None (sem regra)
#   densidade:           (min, max) mm/ponto
#   salto_max:           float mm
#   limite_pontos:       {"min": int, "max": int}
#   descricao:           str
#   variantes:           (opcional, p/ cetim) dict de dials rotativos
#   default:             (opcional) nome da variante padrao

TECIDOS = {
    "malha": {
        "compensacao_exigida": "alta",
        "underlay_exigido": True,
        "densidade": (0.35, 0.45),
        "salto_max": 4.0,
        "limite_pontos": {"min": 0, "max": 20000},
        "descricao": "Malha (algodao/poliester com elastano, estica)",
    },
    "jeans": {
        "compensacao_exigida": "media",
        "underlay_exigido": False,
        "densidade": (0.40, 0.50),
        "salto_max": 5.0,
        "limite_pontos": {"min": 0, "max": 40000},
        "descricao": "Jeans (tecido rigido)",
    },
    "nylon": {
        "compensacao_exigida": "media",
        "underlay_exigido": True,
        "densidade": (0.35, 0.45),
        "salto_max": 4.0,
        "limite_pontos": {"min": 0, "max": 25000},
        "descricao": "Nylon (sintetico, solta ponto)",
    },
    "bone": {
        "compensacao_exigida": "baixa",
        "underlay_exigido": True,
        "densidade": (0.35, 0.45),
        "salto_max": 5.0,
        "limite_pontos": {"min": 0, "max": 15000},
        "descricao": "Bone (casquete curvo, tecido firme)",
    },
    "cetim": {
        "compensacao_exigida": "media",
        "underlay_exigido": False,
        "salto_max": 5.0,
        "limite_pontos": {"min": 0, "max": 20000},
        "descricao": "Cetim (tecido de casamento, fragil). Use --preset ralo|padrao|denso",
        "default": "padrao",
        "variantes": {
            "ralo": {
                "densidade": (0.45, 0.60),
                "compensacao_exigida": "media",
                "underlay_exigido": False,
                "descricao": "Cetim ralo - densidade maior (passo maior) para tecido fino nao rasgar",
            },
            "padrao": {
                "densidade": (0.40, 0.55),
                "compensacao_exigida": "media",
                "underlay_exigido": False,
                "descricao": "Cetim padrao - uso geral",
            },
            "denso": {
                "densidade": (0.35, 0.50),
                "compensacao_exigida": "media",
                "underlay_exigido": False,
                "descricao": "Cetim denso - pontos mais fechados",
            },
        },
        # TODO validar com atelie real os valores de densidade de cada variante
    },
    "generico": {
        "compensacao_exigida": None,
        "underlay_exigido": None,
        "densidade": DENSIDADE_DEFAULT,
        "salto_max": SALTO_DEFAULT_MM,
        "limite_pontos": {"min": 0, "max": 50000},
        "descricao": "Generico (sem regra especifica)",
    },
}


def get_preset(tecido: str = "generico", variante: str = None) -> dict:
    """Resolve o preset efetivo de um tecido, aplicando a variante (dial) quando existir.

    Args:
        tecido: nome do tecido ("malha", "cetim", ...).
        variante: para tecidos com "variantes" (ex: cetim), nome do dial
                  ("ralo", "padrao", "denso"). Usa "default" se None.

    Returns:
        dict com os campos do preset efetivo + "variante_usada".
    """
    tecido = (tecido or "generico").lower()
    base = TECIDOS.get(tecido)
    if base is None:
        base = TECIDOS["generico"]

    if "variantes" in base:
        nome = variante or base.get("default") or "padrao"
        if nome not in base["variantes"]:
            nome = base.get("default") or "padrao"
        v = base["variantes"][nome]
        preset = dict(base)
        preset.pop("variantes", None)
        preset.pop("default", None)
        preset.update(v)
        preset["variante_usada"] = nome
        return preset

    preset = dict(base)
    preset["variante_usada"] = None
    return preset
