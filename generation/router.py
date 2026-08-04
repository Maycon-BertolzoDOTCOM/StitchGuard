"""ProviderRouter — cascata de provedores com fallback (espelho do MaterialView-Pro)."""
from typing import Optional

from .difficulty import estimar_dificuldade
from .providers import cli_anything, wilcom, humano

# costTier: 0 = gratuito, 1 = pago. Ordenado do mais barato para o mais caro.
# InkStitch removido da cascata (stub, ver PENDENCIAS_EXTERNAS.md B).
COST_TIERS = [
    ("cli-anything", cli_anything.generate, 0),
    ("wilcom", wilcom.generate, 1),
    ("humano", humano.generate, 99),
]

# Dificuldade >= threshold usa no minimo este costTier (DifficultyEstimator).
MIN_COST_TIER_BY_DIFFICULTY = {
    "low": 0,
    "medium": 0,
    "high": 1,
}


def _resolver_dificuldade(arte_path: str | None, params: dict, difficulty: str) -> str:
    """Resolve difficulty: se 'auto', calcula a partir da arte; senao usa o valor."""
    if difficulty != "auto":
        return difficulty
    try:
        import json as _json
        if arte_path:
            with open(arte_path, "r", encoding="utf-8") as fh:
                arte = _json.load(fh)
        else:
            arte = {}
    except Exception:
        arte = {}
    return estimar_dificuldade(arte, params)


def route(arte_path: str, params: dict, difficulty: str = "low") -> Optional[str]:
    """Tenta cada provedor elegivel em ordem; para no primeiro sucesso.

    difficulty="auto" calcula a dificuldade a partir da arte (DifficultyEstimator).
    Provedores com costTier < minimo sao pulados para tarefas dificeis.
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
