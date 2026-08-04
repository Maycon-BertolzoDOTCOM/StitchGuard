"""Testes unitários de generation/difficulty.py (DifficultyEstimator)."""
from generation.difficulty import estimar_dificuldade


def test_arte_pequena_poucas_cores_low():
    arte = {"largura_mm": 50, "altura_mm": 50, "objetos": [{"cor": 0}, {"cor": 1}]}
    assert estimar_dificuldade(arte) == "low"


def test_arte_media_cores_medias_medium():
    arte = {"largura_mm": 150, "altura_mm": 150, "objetos": [{"cor": i} for i in range(5)]}
    assert estimar_dificuldade(arte) == "medium"


def test_arte_grande_muitas_cores_high():
    arte = {"largura_mm": 400, "altura_mm": 400, "objetos": [{"cor": i} for i in range(10)]}
    assert estimar_dificuldade(arte) == "high"


def test_bone_adiciona_dificuldade():
    arte = {"largura_mm": 50, "altura_mm": 50, "objetos": [{"cor": 0}]}
    assert estimar_dificuldade(arte, {"tecido": "bone"}) == "medium"


def test_jeans_adiciona_ponto():
    arte = {"largura_mm": 50, "altura_mm": 50, "objetos": [{"cor": i} for i in range(4)]}
    assert estimar_dificuldade(arte, {"tecido": "jeans"}) == "medium"


def test_arte_vazia_low():
    assert estimar_dificuldade({}) == "low"


def test_muitos_objetos_medio():
    arte = {"largura_mm": 50, "altura_mm": 50, "objetos": [{"cor": i} for i in range(15)]}
    assert estimar_dificuldade(arte) == "medium"


def test_muitos_objetos_grandes_high():
    arte = {"largura_mm": 350, "altura_mm": 350, "objetos": [{"cor": i} for i in range(25)]}
    assert estimar_dificuldade(arte) == "high"
