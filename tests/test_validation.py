"""Testes unitários de validation: checklist (scores individuais) e metrics."""
import os
import pyembroidery as pe

from validation.checklist import (
    SCORE_GLOBAL_MIN, run_checklist,
    _score_tecido, _score_compensacao, _score_amarracao, _score_densidade,
    _score_saltos, _score_nos, _score_limite_pontos,
    _score_limite_cores, _score_cabe_aro,
)
from validation.metrics import StitchMetrics

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "limpo.dst")


def _criar_pattern_simples():
    p = pe.EmbPattern()
    p.add_thread(pe.EmbThread(0))
    p.add_stitch_absolute(pe.STOP, 0, 0)
    for x in range(20):
        p.add_stitch_absolute(pe.STITCH, x * 0.4, 0)
    p.add_stitch_absolute(pe.STOP, 0, 0)
    caminho = "/tmp/_test_simples.dst"
    pe.write(p, caminho)
    return caminho


def _criar_pattern_com_saltos_grandes():
    p = pe.EmbPattern()
    p.add_thread(pe.EmbThread(0))
    p.add_stitch_absolute(pe.STOP, 0, 0)
    p.add_stitch_absolute(pe.STITCH, 0, 0)
    p.add_stitch_absolute(pe.STITCH, 50, 0)  # salto 50mm
    caminho = "/tmp/_test_saltos.dst"
    pe.write(p, caminho)
    return caminho


# --- scores individuais ---

def test_score_tecido_informado():
    r = _score_tecido({"tecido": "jeans"})
    assert r["score"] == 1.0
    assert r["aprovado"] is True


def test_score_tecido_ausente():
    r = _score_tecido({})
    assert r["score"] is None


def test_score_compensacao_correta():
    metrics = StitchMetrics(FIXTURE)
    r = _score_compensacao(metrics, {"tecido": "nylon", "compensacao": "media"})
    assert r["score"] == 1.0


def test_score_compensacao_errada():
    metrics = StitchMetrics(FIXTURE)
    r = _score_compensacao(metrics, {"tecido": "nylon", "compensacao": "baixa"})
    assert r["score"] == 0.3


def test_score_underlay_correto():
    metrics = StitchMetrics(FIXTURE)
    r = _score_amarracao(metrics, {"tecido": "malha", "underlay": True})
    assert r["score"] == 1.0


def test_score_underlay_errado():
    metrics = StitchMetrics(FIXTURE)
    r = _score_amarracao(metrics, {"tecido": "malha", "underlay": False})
    assert r["score"] == 0.3


def test_score_nos_paradas():
    metrics = StitchMetrics(FIXTURE)
    r = _score_nos(metrics, {})
    assert r["score"] >= 0.5


def test_score_limite_pontos():
    metrics = StitchMetrics(FIXTURE)
    r = _score_limite_pontos(metrics, {"tecido": "nylon"})
    assert r["score"] == 1.0


def test_score_limite_cores_sem_maquina():
    metrics = StitchMetrics(FIXTURE)
    r = _score_limite_cores(metrics, {})
    assert r["score"] is None


def test_score_cabe_aro_sem_maquina():
    metrics = StitchMetrics(FIXTURE)
    r = _score_cabe_aro(metrics, {})
    assert r["score"] is None


# --- run_checklist ---

def test_checklist_completo():
    metrics = StitchMetrics(FIXTURE)
    r = run_checklist(metrics, {"tecido": "nylon", "compensacao": "media", "underlay": True})
    assert r["score_global"] >= SCORE_GLOBAL_MIN
    assert r["aprovado"] is True
    assert len(r["itens"]) == 11


def test_checklist_com_maquina():
    metrics = StitchMetrics(FIXTURE)
    r = run_checklist(metrics, {
        "tecido": "nylon", "compensacao": "media",
        "underlay": True, "maquina_id": "generica",
    })
    assert r["aprovado"] is True
    assert r["itens"]["limite_cores"]["score"] == 1.0
    assert r["itens"]["cabe_no_aro"]["score"] == 1.0


def test_checklist_itens_pendentes_revisao():
    metrics = StitchMetrics(FIXTURE)
    r = run_checklist(metrics, {"tecido": "nylon"})
    pendentes = r["itens_pendentes_revisao_humana"]
    assert "ordem_costura" in pendentes
    assert "angulos_satin" in pendentes


# --- metrics ---

def test_metrics_stitch_count():
    m = StitchMetrics(FIXTURE)
    assert m.stitch_count > 0


def test_metrics_bounding_box():
    m = StitchMetrics(FIXTURE)
    assert m.width_mm > 0
    assert m.height_mm > 0


def test_metrics_average_stitch_length():
    m = StitchMetrics(FIXTURE)
    assert m.average_stitch_length_mm() > 0


def test_metrics_max_jump():
    m = StitchMetrics(FIXTURE)
    assert m.max_jump_mm() >= 0


def test_metrics_stops():
    m = StitchMetrics(FIXTURE)
    assert m.stops() >= 2


def test_metrics_blocos_centros():
    m = StitchMetrics(FIXTURE)
    centros = m.blocos_centros()
    assert len(centros) >= 1
    assert all(isinstance(c, tuple) and len(c) == 2 for c in centros)


# --- Edge cases: scores ---

def test_score_saltos_dentro_limite():
    """Saltos dentro do limite do preset devem ter score 1.0."""
    metrics = StitchMetrics(FIXTURE)
    r = _score_saltos(metrics, {"tecido": "nylon"})
    assert r["score"] == 1.0


def test_score_saltos_com_maquina_generica():
    """Com maquina generica (max_salto 300), limite vem do preset."""
    metrics = StitchMetrics(FIXTURE)
    r = _score_saltos(metrics, {"tecido": "nylon", "maquina_id": "generica"})
    assert r["score"] == 1.0


def test_score_densidade_dentro_faixa():
    """Densidade dentro da faixa do preset (usando jeans que aceita 0.40-0.50)."""
    metrics = StitchMetrics(FIXTURE)
    r = _score_densidade(metrics, {"tecido": "jeans"})
    assert r["score"] == 1.0


def test_score_tecido_desconhecido():
    """Tecido nao listado usa preset generico e retorna score 1.0 (tecido informado)."""
    r = _score_tecido({"tecido": "fibra_avancada"})
    assert r["score"] == 1.0


def test_checklist_score_global_fracionario():
    """Score global deve ser fracionario, nao apenas 0/0.5/1."""
    metrics = StitchMetrics(FIXTURE)
    r = run_checklist(metrics, {"tecido": "nylon", "compensacao": "media", "underlay": True})
    assert isinstance(r["score_global"], float)
    assert 0.0 <= r["score_global"] <= 1.0
