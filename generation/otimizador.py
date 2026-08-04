"""Otimizador de sequencia de costura — greedy TSP (vizinho mais proximo).

Recebe uma lista de objetos (blocos) com coordenadas (x, y) e retorna a
ordem reordenada para minimizar saltos (conecta ao item 5 do checklist).
"""
import math


def distancia(a, b):
    """Distancia euclidiana entre dois pontos."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _centro(obj):
    """Extrai (x, y) de um objeto: atributos x_centro/y_centro ou tupla."""
    if hasattr(obj, "x_centro") and hasattr(obj, "y_centro"):
        return (obj.x_centro, obj.y_centro)
    if isinstance(obj, (list, tuple)) and len(obj) >= 2:
        return (obj[0], obj[1])
    raise TypeError("Objeto sem coordenadas acessiveis (x_centro/y_centro ou [0]/[1]).")


def otimizar_sequencia(objetos):
    """Reordena objetos por vizinho mais proximo (greedy TSP).

    Retorna lista de indices na nova ordem.
    """
    n = len(objetos)
    if n <= 1:
        return list(range(n))
    centros = [_centro(o) for o in objetos]
    visitados = [False] * n
    ordem = []
    atual = 0
    for _ in range(n):
        ordem.append(atual)
        visitados[atual] = True
        melhor, melhor_dist = None, float("inf")
        for i in range(n):
            if not visitados[i]:
                d = distancia(centros[atual], centros[i])
                if d < melhor_dist:
                    melhor_dist, melhor = d, i
        if melhor is not None:
            atual = melhor
    return ordem


def calcular_saltos(objetos, ordem):
    """Total de saltos (soma das distancias entre objetos consecutivos)."""
    if len(ordem) <= 1:
        return 0.0
    centros = [_centro(o) for o in objetos]
    total = 0.0
    for i in range(len(ordem) - 1):
        total += distancia(centros[ordem[i]], centros[ordem[i + 1]])
    return round(total, 2)


def relatorio_otimizacao(objetos):
    """Relatorio: saltos antes/depois e melhoria."""
    if not objetos:
        return {
            "original": 0.0,
            "otimizado": 0.0,
            "melhoria": 0.0,
            "percentual": 0.0,
            "ordem_original": [],
            "ordem_otimizada": [],
        }
    ordem_original = list(range(len(objetos)))
    ordem_otimizada = otimizar_sequencia(objetos)
    original = calcular_saltos(objetos, ordem_original)
    otimizado = calcular_saltos(objetos, ordem_otimizada)
    melhoria = round(original - otimizado, 2)
    percentual = round((melhoria / original * 100), 1) if original > 0 else 0.0
    return {
        "original": original,
        "otimizado": otimizado,
        "melhoria": melhoria,
        "percentual": percentual,
        "ordem_original": ordem_original,
        "ordem_otimizada": ordem_otimizada,
    }
