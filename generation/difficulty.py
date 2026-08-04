"""DifficultyEstimator — classifica a complexidade da arte para roteamento.

Fatores (do blueprint seção 2.2):
  - Tamanho da arte (mm)
  - Número de cores
  - Número de objetos (proxy para pontos estimados)
  - Tecido (boné = mais difícil)

Retorna "low", "medium" ou "high".
"""


def estimar_dificuldade(arte: dict, params: dict | None = None) -> str:
    """Computa dificuldade a partir da arte e parametros.

    Args:
        arte: dict com largura_mm, altura_mm, objetos.
        params: dict com tecido.

    Returns:
        "low", "medium" ou "high".
    """
    score = 0
    params = params or {}

    # Tamanho da arte
    w = arte.get("largura_mm", 0)
    h = arte.get("altura_mm", 0)
    max_dim = max(w, h)
    if max_dim > 300:
        score += 2
    elif max_dim > 100:
        score += 1

    # Numero de cores
    objetos = arte.get("objetos", [])
    cores = len(set(obj.get("cor", i) for i, obj in enumerate(objetos)))
    if cores > 8:
        score += 2
    elif cores > 3:
        score += 1

    # Numero de objetos (proxy para pontos estimados)
    n_obj = len(objetos)
    if n_obj > 20:
        score += 2
    elif n_obj > 8:
        score += 1

    # Tecido dificil
    tecido = params.get("tecido", "")
    if tecido == "bone":
        score += 2
    elif tecido in ("jeans", "nylon"):
        score += 1

    # Decisao
    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    return "low"
