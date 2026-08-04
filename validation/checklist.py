"""StitchGuard - Checklist de 11 itens (validador gerador-verificador)."""
from domain.maquinas import get_maquina
from domain.presets import get_preset
from generation.otimizador import relatorio_otimizacao

SCORE_GLOBAL_MIN = 0.85

ITENS = {
    1: "tipo_tecido",
    2: "compensacao",
    3: "amarracao",
    4: "densidade",
    5: "saltos",
    6: "ordem_costura",
    7: "angulos_satin",
    8: "nos_lock",
    9: "limite_pontos",
    10: "limite_cores",
    11: "cabe_no_aro",
}


def _preset(params, variante=None):
    tecido = (params or {}).get("tecido", "generico")
    return get_preset(tecido, variante if variante is not None else (params or {}).get("preset"))


def _score_tecido(params):
    if not params or not params.get("tecido"):
        return {"score": None, "aprovado": False, "detalhe": "Tecido nao informado (validador humano)."}
    preset = _preset(params)
    variante = preset.get("variante_usada")
    detalhe = f"Tecido '{params['tecido']}' reconhecido."
    if variante:
        detalhe += f" Variante: {variante}."
    return {"score": 1.0, "aprovado": True, "detalhe": detalhe}


def _score_compensacao(metrics, params):
    compensacao = (params or {}).get("compensacao")
    if not compensacao:
        return {"score": None, "aprovado": False, "detalhe": "Compensacao nao informada (depende de tecido)."}
    preset = _preset(params)
    exigido = preset["compensacao_exigida"]
    variante = preset.get("variante_usada")
    if exigido is None:
        return {"score": 1.0, "aprovado": True, "detalhe": f"Compensacao {compensacao} informada (sem regra p/ {params.get('tecido')})."}
    if compensacao == exigido:
        return {"score": 1.0, "aprovado": True, "detalhe": f"Compensacao {compensacao} correta p/ {params.get('tecido')} (esperado {exigido})."}
    return {"score": 0.3, "aprovado": False, "detalhe": f"Compensacao {compensacao} inadequada p/ {params.get('tecido')} (esperado {exigido})."}


def _score_amarracao(metrics, params):
    underlay = (params or {}).get("underlay")
    if underlay is None:
        return {"score": None, "aprovado": False, "detalhe": "Underlay nao informado."}
    preset = _preset(params)
    exigido = preset["underlay_exigido"]
    if exigido is None:
        return {"score": 1.0 if underlay else 0.0, "aprovado": bool(underlay), "detalhe": f"Underlay {'ativo' if underlay else 'ausente'} (sem regra p/ {params.get('tecido')})."}
    if underlay == exigido:
        return {"score": 1.0, "aprovado": True, "detalhe": f"Underlay {'ativo' if underlay else 'ausente'} correto p/ {params.get('tecido')}."}
    return {"score": 0.3, "aprovado": False, "detalhe": f"Underlay {'ativo' if underlay else 'ausente'} inadequado p/ {params.get('tecido')} (esperado {'ativo' if exigido else 'ausente'})."}


def _score_densidade(metrics, params):
    passo_mm = metrics.average_stitch_length_mm()
    if passo_mm <= 0:
        return {"score": 0.0, "aprovado": False, "detalhe": "Sem comprimento de ponto calculavel."}
    preset = _preset(params)
    lo, hi = preset["densidade"]
    variante = preset.get("variante_usada")
    extra = f" (variante {variante})" if variante else ""
    if lo <= passo_mm <= hi:
        return {"score": 1.0, "aprovado": True, "detalhe": f"Passo medio {passo_mm:.2f}mm/ponto dentro de [{lo}, {hi}] p/ {params.get('tecido')}{extra}."}
    return {"score": 0.3, "aprovado": False, "detalhe": f"Passo medio {passo_mm:.2f}mm/ponto fora de [{lo}, {hi}] p/ {params.get('tecido')}{extra}."}


def _score_saltos(metrics, params):
    max_jump = metrics.max_jump_mm()
    limite_preset = _preset(params)["salto_max"]
    maquina = get_maquina((params or {}).get("maquina_id"))
    limite = min(limite_preset, maquina.get("max_salto_mm", limite_preset))
    detalhe = f"Maior salto {max_jump}mm < {limite}mm (limite {params.get('tecido')} x {maquina['maquina_id']})."
    if max_jump <= limite:
        return {"score": 1.0, "aprovado": True, "detalhe": detalhe}
    return {"score": 0.2, "aprovado": False, "detalhe": f"Maior salto {max_jump}mm >= {limite}mm (limite {params.get('tecido')} x {maquina['maquina_id']})."}


def _score_ordem(metrics):
    return {"score": None, "aprovado": False, "detalhe": "Ordem de costura requer analise visual (humano)."}


def _score_satin(metrics):
    return {"score": None, "aprovado": False, "detalhe": "Angulos do satin requerem analise visual (humano)."}


def _score_nos(metrics, params):
    stops = metrics.stops()
    if stops >= 2:
        resultado = {"score": 1.0, "aprovado": True, "detalhe": f"{stops} paradas detectadas (lock stitch presumido)."}
    else:
        resultado = {"score": 0.5, "aprovado": False, "detalhe": f"{stops} paradas - verificar lock stitch manualmente."}
    maquina = get_maquina((params or {}).get("maquina_id"))
    if not maquina.get("suporta_trim", True):
        resultado["detalhe"] += f" | ATENCAO: maquina sem trim ({maquina['maquina_id']}), verificar nos extras apos saltos."
        resultado["score"] = min(resultado["score"], 0.5)
    return resultado


def _score_limite_pontos(metrics, params):
    preset = _preset(params)
    limites = preset["limite_pontos"]
    total = metrics.stitch_count
    if limites["min"] <= total <= limites["max"]:
        return {"score": 1.0, "aprovado": True, "detalhe": f"{total} pontos dentro do limite."}
    return {"score": 0.3, "aprovado": False, "detalhe": f"{total} pontos fora de [{limites['min']}, {limites['max']}]."}


def _score_limite_cores(metrics, params):
    """Item 10: numero de cores da arte <= agulhas da maquina."""
    if not (params or {}).get("maquina_id"):
        return {"score": None, "aprovado": True, "detalhe": "Maquina nao informada (item ignorado)."}
    maquina = get_maquina(params["maquina_id"])
    try:
        cores = len(list(metrics.pattern.get_as_colorblocks()))
    except Exception:
        return {"score": None, "aprovado": True, "detalhe": "Nao foi possivel contar cores (item ignorado)."}
    if cores <= maquina["agulhas"]:
        return {"score": 1.0, "aprovado": True, "detalhe": f"{cores} cores <= {maquina['agulhas']} agulhas ({maquina['maquina_id']})."}
    return {"score": 0.3, "aprovado": False, "detalhe": f"{cores} cores > {maquina['agulhas']} agulhas ({maquina['maquina_id']})."}


def _score_cabe_aro(metrics, params):
    """Item 11: dimensoes da matriz cabem no campo/aro da maquina."""
    if not (params or {}).get("maquina_id"):
        return {"score": None, "aprovado": True, "detalhe": "Maquina nao informada (item ignorado)."}
    maquina = get_maquina(params["maquina_id"])
    largura, altura = metrics.width_mm, metrics.height_mm
    if largura <= maquina["campo_largura"] and altura <= maquina["campo_altura"]:
        return {"score": 1.0, "aprovado": True,
                "detalhe": f"{largura:.1f}x{altura:.1f}mm cabe no aro {maquina['campo_largura']}x{maquina['campo_altura']}mm ({maquina['maquina_id']})."}
    return {"score": 0.3, "aprovado": False,
            "detalhe": f"{largura:.1f}x{altura:.1f}mm excede aro {maquina['campo_largura']}x{maquina['campo_altura']}mm ({maquina['maquina_id']})."}


def run_checklist(metrics, params=None):
    params = params or {}
    resultados = {
        ITENS[1]: _score_tecido(params),
        ITENS[2]: _score_compensacao(metrics, params),
        ITENS[3]: _score_amarracao(metrics, params),
        ITENS[4]: _score_densidade(metrics, params),
        ITENS[5]: _score_saltos(metrics, params),
        ITENS[6]: _score_ordem(metrics),
        ITENS[7]: _score_satin(metrics),
        ITENS[8]: _score_nos(metrics, params),
        ITENS[9]: _score_limite_pontos(metrics, params),
        ITENS[10]: _score_limite_cores(metrics, params),
        ITENS[11]: _score_cabe_aro(metrics, params),
    }
    automaticos = [r for r in resultados.values() if r["score"] is not None]
    scores = [r["score"] for r in automaticos]
    score_global = round(sum(scores) / len(scores), 2) if scores else 0.0
    aprovado_global = score_global >= SCORE_GLOBAL_MIN
    pendentes = [k for k, r in resultados.items() if r["score"] is None]

    otimizacao = None
    try:
        blocos = metrics.blocos_centros()
        if len(blocos) > 1:
            otimizacao = relatorio_otimizacao(blocos)
    except Exception:
        otimizacao = None

    return {
        "score_global": score_global,
        "aprovado": aprovado_global,
        "itens": resultados,
        "itens_pendentes_revisao_humana": pendentes,
        "otimizacao_saltos": otimizacao,
    }
