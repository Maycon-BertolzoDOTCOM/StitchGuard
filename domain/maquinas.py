"""Catálogo de máquinas de bordado — fonte única de verdade para limites físicos."""

MAQUINAS = {
    # Industrial
    "tajima-tfmx-6": {
        "marca": "Tajima",
        "modelo": "TFMX-6",
        "agulhas": 6,
        "formato_nativo": "dst",
        "campo_largura": 360,
        "campo_altura": 300,
        "suporta_trim": True,
        "max_ponto_mm": 12.1,
        "max_salto_mm": 12.0,
        "comando_troca": "COLOR_CHANGE",
        "tipo": "industrial",
    },
    "tajima-tfmx-4": {
        "marca": "Tajima",
        "modelo": "TFMX-4",
        "agulhas": 4,
        "formato_nativo": "dst",
        "campo_largura": 360,
        "campo_altura": 300,
        "suporta_trim": True,
        "max_ponto_mm": 12.1,
        "max_salto_mm": 12.0,
        "comando_troca": "COLOR_CHANGE",
        "tipo": "industrial",
    },
    "tajima-tfmx-9": {
        "marca": "Tajima",
        "modelo": "TFMX-9",
        "agulhas": 9,
        "formato_nativo": "dst",
        "campo_largura": 360,
        "campo_altura": 300,
        "suporta_trim": True,
        "max_ponto_mm": 12.1,
        "max_salto_mm": 12.0,
        "comando_troca": "COLOR_CHANGE",
        "tipo": "industrial",
    },
    # Domésticas
    "brother-pr1050x": {
        "marca": "Brother",
        "modelo": "PR1050X",
        "agulhas": 6,
        "formato_nativo": "pes",
        "campo_largura": 200,
        "campo_altura": 200,
        "suporta_trim": True,
        "max_ponto_mm": 10.0,
        "max_salto_mm": 8.0,
        "comando_troca": "COLOR_CHANGE",
        "tipo": "domestica",
    },
    "brother-pr680w": {
        "marca": "Brother",
        "modelo": "PR680W",
        "agulhas": 6,
        "formato_nativo": "pes",
        "campo_largura": 200,
        "campo_altura": 200,
        "suporta_trim": True,
        "max_ponto_mm": 10.0,
        "max_salto_mm": 8.0,
        "comando_troca": "COLOR_CHANGE",
        "tipo": "domestica",
    },
    "janome-mb-4": {
        "marca": "Janome",
        "modelo": "MB-4",
        "agulhas": 4,
        "formato_nativo": "jef",
        "campo_largura": 160,
        "campo_altura": 160,
        "suporta_trim": True,
        "max_ponto_mm": 8.0,
        "max_salto_mm": 6.0,
        "comando_troca": "COLOR_CHANGE",
        "tipo": "domestica",
    },
    "singer-xl-400": {
        "marca": "Singer",
        "modelo": "XL-400",
        "agulhas": 1,
        "formato_nativo": "vp3",
        "campo_largura": 120,
        "campo_altura": 120,
        "suporta_trim": False,
        "max_ponto_mm": 6.0,
        "max_salto_mm": 4.0,
        "comando_troca": "COLOR_CHANGE",
        "tipo": "domestica",
    },
    # Máquinas alternativas
    "barudan-6": {
        "marca": "Barudan",
        "modelo": "6-aguilhas",
        "agulhas": 6,
        "formato_nativo": "u01",
        "campo_largura": 300,
        "campo_altura": 250,
        "suporta_trim": True,
        "max_ponto_mm": 12.1,
        "max_salto_mm": 12.0,
        "comando_troca": "NEEDLE_SET",
        "tipo": "industrial",
    },
    "melco-4": {
        "marca": "Melco",
        "modelo": "4-aguilhas",
        "agulhas": 4,
        "formato_nativo": "exp",
        "campo_largura": 250,
        "campo_altura": 200,
        "suporta_trim": True,
        "max_ponto_mm": 12.1,
        "max_salto_mm": 12.0,
        "comando_troca": "COLOR_CHANGE",
        "tipo": "industrial",
    },
    "pfaff-5": {
        "marca": "Pfaff",
        "modelo": "5-aguilhas",
        "agulhas": 5,
        "formato_nativo": "vp3",
        "campo_largura": 200,
        "campo_altura": 200,
        "suporta_trim": True,
        "max_ponto_mm": 8.0,
        "max_salto_mm": 6.0,
        "comando_troca": "COLOR_CHANGE",
        "tipo": "industrial",
    },
    "generica": {
        "marca": "Genérica",
        "modelo": "6-aguilhas",
        "agulhas": 6,
        "formato_nativo": "dst",
        "campo_largura": 300,
        "campo_altura": 300,
        "suporta_trim": True,
        "max_ponto_mm": 12.1,
        "max_salto_mm": 12.1,
        "comando_troca": "COLOR_CHANGE",
        "tipo": "indefinido",
    },
}


def _resolver_id(maquina_id):
    """Resolve um ID: exato, match parcial ou generica."""
    if maquina_id is None:
        return "generica"
    if maquina_id in MAQUINAS:
        return maquina_id
    possiveis = [k for k in MAQUINAS if maquina_id.lower() in k.lower()]
    return possiveis[0] if possiveis else "generica"


def get_maquina(maquina_id: str = None) -> dict:
    """Retorna o preset da máquina, com fallback para 'generica'.

    Args:
        maquina_id: ID do catálogo (ex.: 'tajima-tfmx-6'). None ou desconhecido
                    resolve para a genérica (com match parcial como conveniência).

    Returns:
        Cópia do dict da máquina, sempre com a chave 'maquina_id'.
    """
    resolvido = _resolver_id(maquina_id)
    result = dict(MAQUINAS[resolvido])
    result["maquina_id"] = resolvido
    return result


def listar_maquinas() -> list:
    """Retorna lista de IDs de máquinas disponíveis (exclui a genérica)."""
    return sorted(k for k in MAQUINAS if k != "generica")


def formatar_maquina(maquina: dict) -> str:
    """Formata o preset da máquina para exibição."""
    return f"{maquina['marca']} {maquina['modelo']} ({maquina['agulhas']} agulhas, {maquina['formato_nativo']})"
