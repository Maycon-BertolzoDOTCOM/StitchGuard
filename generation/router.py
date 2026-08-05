"""ProviderRouter — cascata de provedores com fallback.

Provedores em ordem de custo (do mais barado ao mais caro):
1. cli-anything (pyembroidery) — gratuito
2. inkstitch (auto-digitizing) — gratuito
3. wilcom (API) — pago
4. humano (último recurso)
"""
import os
import uuid
import tempfile
from typing import Optional

import structlog
from .difficulty import estimar_dificuldade
from .providers import cli_anything, wilcom, humano

log = structlog.get_logger()


def _inkstitch_generate(arte_path: str | None, params: dict) -> Optional[str]:
    """Gera .dst usando Ink/Stitch auto-digitizing."""
    if not arte_path:
        return None

    # Verificar se é imagem (PNG/JPG)
    ext = os.path.splitext(arte_path)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
        return None

    try:
        from generation.inkstitch_provider import auto_digitize
        import pyembroidery as pe
    except ImportError:
        return None

    try:
        tecido = params.get("tecido", "generico")
        pontos = auto_digitize(arte_path, tecido=tecido)

        if not pontos:
            return None

        # Converter para EmbPattern
        pattern = pe.EmbPattern()
        for p in pontos:
            tipo = p.get("type", "STITCH")
            if tipo == "JUMP":
                pattern.add_stitch_absolute(pe.JUMP, p["x"], p["y"])
            elif tipo == "TRIM":
                pattern.add_stitch_absolute(pe.TRIM, p["x"], p["y"])
            else:
                pattern.add_stitch_absolute(pe.STITCH, p["x"], p["y"])

        pattern.add_command(pe.END)

        # Salvar .dst
        dst_path = os.path.join(tempfile.gettempdir(), f"inkstitch_{uuid.uuid4().hex[:8]}.dst")
        pe.write(pattern, dst_path)

        return dst_path
    except Exception as e:
        log.error("inkstitch.erro", erro=str(e))
        return None


# costTier: 0 = gratuito, 1 = pago
COST_TIERS = [
    ("cli-anything", cli_anything.generate, 0),
    ("inkstitch", _inkstitch_generate, 0),
    ("wilcom", wilcom.generate, 1),
    ("humano", humano.generate, 99),
]

# Dificuldade >= threshold usa no minimo este costTier
MIN_COST_TIER_BY_DIFFICULTY = {
    "low": 0,
    "medium": 0,
    "high": 0,  # Ink/Stitch agora suporta alta dificuldade
}


def _resolver_dificuldade(arte_path: str | None, params: dict, difficulty: str) -> str:
    """Resolve difficulty: se 'auto', calcula a partir da arte; senao usa o valor."""
    if difficulty != "auto":
        return difficulty
    try:
        import json as _json
        if arte_path:
            with open(arte_path, "r", encoding="utf-8") as fh:
                arte = _json.load(arte)
        else:
            arte = {}
    except Exception:
        arte = {}
    return estimar_dificuldade(arte, params)


def route(arte_path: str, params: dict, difficulty: str = "low") -> Optional[str]:
    """Tenta cada provedor elegivel em ordem; para no primeiro sucesso.

    difficulty="auto" calcula a dificuldade a partir da arte (DifficultyEstimator).
    """
    difficulty = _resolver_dificuldade(arte_path, params, difficulty)
    min_tier = MIN_COST_TIER_BY_DIFFICULTY.get(difficulty, 0)

    for name, provider, cost_tier in COST_TIERS:
        if cost_tier < min_tier:
            continue
        try:
            result = provider(arte_path, params)
            if result:
                return result
        except Exception:
            continue

    raise RuntimeError("Todos os provedores falharam — fallback humano nao disponivel.")
