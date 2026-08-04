"""Testes unitários de generation: otimizador, router, cli_anything."""
import pyembroidery as pe

from generation.otimizador import (
    distancia, otimizar_sequencia, calcular_saltos, relatorio_otimizacao,
)
from generation.router import route, MIN_COST_TIER_BY_DIFFICULTY
from generation.providers.cli_anything import AMOSTRA_DEFAULT


# --- otimizador ---

def test_distancia():
    assert distancia((0, 0), (3, 4)) == 5.0


def test_otimizar_um_elemento():
    assert otimizar_sequencia([(0, 0)]) == [0]


def test_otimizar_dois_elementos():
    r = otimizar_sequencia([(0, 0), (10, 0)])
    assert r == [0, 1]


def test_otimizar_tres_elementos():
    pts = [(0, 0), (10, 0), (5, 10)]
    r = otimizar_sequencia(pts)
    assert len(r) == 3
    assert set(r) == {0, 1, 2}


def test_calcular_saltos_zero():
    assert calcular_saltos([(0, 0)], [0]) == 0.0


def test_calcular_saltos():
    assert calcular_saltos([(0, 0), (3, 4)], [0, 1]) == 5.0


def test_relatorio_otimizacao_vazio():
    r = relatorio_otimizacao([])
    assert r["original"] == 0.0
    assert r["percentual"] == 0.0


def test_relatorio_otimizacao_reduz():
    pts = [(0, 0), (100, 0), (0, 100)]
    r = relatorio_otimizacao(pts)
    assert r["melhoria"] >= 0
    assert r["percentual"] >= 0


# --- router ---

def test_route_falha_todos_provedores():
    """Todos os provedores são stubs exceto cli_anything; route não deve falhar."""
    result = route(None, {"tecido": "jeans"})
    assert result is not None
    assert result.endswith(".dst")


def test_route_difficulty_high_pula_cost_tier_0():
    """Difficulty high deve pular provedores cost 0; cli_anything é cost 0,
    então route deve falhar (todos pulados)."""
    # cli_anything é cost 0, os outros são stubs
    # difficulty high → min_tier=1 → cli_anything pulado → todos stubs falham
    try:
        result = route(None, {"tecido": "jeans"}, difficulty="high")
        # Se chegar aqui, cli_anything não foi pulado (bug) ou algum stub funcionou
        assert result is None or not result
    except RuntimeError:
        pass  # Esperado: todos os provedores falharam


def test_min_cost_tier():
    assert MIN_COST_TIER_BY_DIFFICULTY["low"] == 0
    assert MIN_COST_TIER_BY_DIFFICULTY["medium"] == 0
    assert MIN_COST_TIER_BY_DIFFICULTY["high"] == 1


# --- cli_anything ---

def test_amostra_default_tem_objetos():
    assert "objetos" in AMOSTRA_DEFAULT
    assert len(AMOSTRA_DEFAULT["objetos"]) >= 1


def test_cli_anything_gera_dst(tmp_path):
    out = tmp_path / "test.dst"
    from generation.providers.cli_anything import generate
    result = generate(None, {"tecido": "jeans"})
    assert result.endswith(".dst")
    import os
    assert os.path.exists(result)
