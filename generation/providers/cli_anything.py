"""Provedor cli-anything-inkstitch — geração local de rascunho via pyembroidery (costTier 0).

Converte o JSON de arte (formas geométricas em mm) em uma matriz .dst usando
o núcleo de digitalização de generation.rascunho e os presets de tecido.
É o "provedor interno" do MVP: dispensa Inkscape/InkStitch e torna o
ProviderRouter funcional de ponta a ponta.
"""
import json
import os

import pyembroidery as pe

from domain.presets import get_preset
from generation.rascunho import rastrear_bloco

AMOSTRA_DEFAULT = {
    "nome": "Amostra 4 blocos (demonstracao)",
    "largura_mm": 6.0,
    "altura_mm": 6.0,
    "objetos": [
        {"tipo": "retangulo", "x": 0.0, "y": 0.0, "largura": 1.5, "altura": 1.5, "cor": 0},
        {"tipo": "retangulo", "x": 2.5, "y": 2.5, "largura": 1.5, "altura": 1.5, "cor": 1},
        {"tipo": "retangulo", "x": 0.0, "y": 2.5, "largura": 1.5, "altura": 1.5, "cor": 2},
        {"tipo": "retangulo", "x": 2.5, "y": 0.0, "largura": 1.5, "altura": 1.5, "cor": 3},
    ],
}


def _carregar_arte(arte_path):
    """Carrega o JSON de arte; usa a amostra padrão quando não informado."""
    if not arte_path:
        return AMOSTRA_DEFAULT
    with open(arte_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _origem(forma):
    """Ponto de origem do bloco (onde o lock stitch começa)."""
    return (
        forma.get("x", forma.get("centro_x", 0.0)),
        forma.get("y", forma.get("centro_y", 0.0)),
    )


def _ultima_posicao(pattern):
    """Posição do último comando adicionado (para STOP/JUMP sem salto falso)."""
    if not pattern.stitches:
        return (0.0, 0.0)
    return (pattern.stitches[-1][0], pattern.stitches[-1][1])


def _construir_pattern(arte, preset):
    """Constrói o EmbPattern a partir do JSON de arte (um bloco por objeto).

    Transições entre blocos: TRIM->JUMP->STOP na origem do próximo bloco.
    Um STOP inicial (troca p/ primeira cor) garante >= 2 paradas (item 8).
    """
    pattern = pe.EmbPattern()
    for i, obj in enumerate(arte["objetos"]):
        cor = int(obj.get("cor", i))
        pattern.add_thread(pe.EmbThread(cor))
        orig_x, orig_y = _origem(obj)
        if i > 0:
            pattern.add_stitch_absolute(pe.JUMP, orig_x, orig_y)
        pattern.add_stitch_absolute(pe.STOP, orig_x, orig_y)
        rastrear_bloco(pattern, obj, preset)
    fim_x, fim_y = _ultima_posicao(pattern)
    pattern.add_stitch_absolute(pe.STOP, fim_x, fim_y)
    return pattern


def generate(arte_path: str, params: dict) -> str:
    """Gera uma matriz .dst a partir do JSON de arte.

    Args:
        arte_path: caminho do JSON de arte (None => amostra padrão).
        params: dict com tecido/preset/compensacao/underlay.

    Returns:
        Caminho absoluto do .dst gerado.
    """
    preset = get_preset((params or {}).get("tecido"), (params or {}).get("preset"))
    arte = _carregar_arte(arte_path)
    pattern = _construir_pattern(arte, preset)

    if arte_path:
        out = os.path.splitext(arte_path)[0] + ".dst"
    else:
        out = os.path.abspath(os.path.join(os.getcwd(), "amostra.dst"))
    pe.write(pattern, out)
    return out
