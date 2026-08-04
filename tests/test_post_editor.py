"""Testes do post-editor — operações de pós-edição."""
import math
import os
import tempfile

import pyembroidery as pe
import pytest

from post_editor.editor import (
    compensacao_pull,
    ajustar_densidade,
    reordenar_blocos,
    inserir_ponto,
    remover_ponto,
    adicionar_underlay,
    remover_underlay,
    aplicar_operacoes,
)


def _pattern_simples():
    """Cria padrão simples para testes: linha horizontal de 10mm."""
    p = pe.EmbPattern()
    p.add_thread(pe.EmbThread(0x000000))
    for i in range(11):
        p.add_stitch_absolute(pe.STITCH, i * 1.0, 0.0)
    return p


def _pattern_zigzag():
    """Cria padrão em ziguezague para testes."""
    p = pe.EmbPattern()
    p.add_thread(pe.EmbThread(0xFF0000))
    pontos = [
        (0, 0), (1, 1), (2, 0), (3, 1), (4, 0),
        (5, 1), (6, 0), (7, 1), (8, 0),
    ]
    for x, y in pontos:
        p.add_stitch_absolute(pe.STITCH, x, y)
    return p


def _pattern_multi_cor():
    """Cria padrão com múltiplos blocos de cor."""
    p = pe.EmbPattern()
    p.add_thread(pe.EmbThread(0xFF0000))
    p.add_thread(pe.EmbThread(0x00FF00))

    # Bloco 1 (vermelho)
    p.add_stitch_absolute(pe.STITCH, 0, 0)
    p.add_stitch_absolute(pe.STITCH, 5, 0)
    p.add_stitch_absolute(pe.STITCH, 5, 5)

    # COLOR_CHANGE
    p.add_stitch_absolute(pe.COLOR_CHANGE, 5, 5)

    # Bloco 2 (verde)
    p.add_stitch_absolute(pe.STITCH, 10, 0)
    p.add_stitch_absolute(pe.STITCH, 15, 0)
    p.add_stitch_absolute(pe.STITCH, 15, 5)

    return p


def _dst_temporario(pattern):
    """Salva pattern em .dst temporário e retorna caminho."""
    with tempfile.NamedTemporaryFile(suffix=".dst", delete=False) as f:
        pe.write(pattern, f.name)
        return f.name


# ---------------------------------------------------------------------------
# Testes de compensacao_pull
# ---------------------------------------------------------------------------

class TestCompensacaoPull:
    def test_compensacao_pull_retorna_pattern(self):
        p = _pattern_simples()
        result = compensacao_pull(p, valor_mm=0.5)
        assert isinstance(result, pe.EmbPattern)

    def test_compensacao_pull_mantem_pontos(self):
        p = _pattern_simples()
        result = compensacao_pull(p, valor_mm=0.5)
        assert len(list(result.stitches)) == len(list(p.stitches))

    def test_compensacao_pull_zero(self):
        p = _pattern_simples()
        result = compensacao_pull(p, valor_mm=0.0)
        original = list(p.stitches)
        editado = list(result.stitches)
        for o, e in zip(original, editado):
            assert abs(o[0] - e[0]) < 0.01
            assert abs(o[1] - e[1]) < 0.01

    def test_compensacao_pull_vertical(self):
        """Linha vertical deve ser deslocada horizontalmente."""
        p = pe.EmbPattern()
        p.add_thread(pe.EmbThread(0x000000))
        for i in range(6):
            p.add_stitch_absolute(pe.STITCH, 0.0, i * 1.0)

        result = compensacao_pull(p, valor_mm=1.0)
        stitches = list(result.stitches)
        # Primeiro ponto não é deslocado (sem referência anterior)
        # Mas pontos seguintes devem ter coordenada X diferente de 0
        assert any(s[0] != 0.0 for s in stitches[1:])


# ---------------------------------------------------------------------------
# Testes de ajustar_densidade
# ---------------------------------------------------------------------------

class TestAjustarDensidade:
    def test_ajustar_densidade_retorna_pattern(self):
        p = _pattern_simples()
        result = ajustar_densidade(p, fator=0.5)
        assert isinstance(result, pe.EmbPattern)

    def test_ajustar_densidade_mais_denso(self):
        p = _pattern_simples()
        result = ajustar_densidade(p, fator=0.5)
        # Distância entre pontos deve ser menor
        stitches_orig = list(p.stitches)
        stitches_edit = list(result.stitches)
        dist_orig = math.hypot(stitches_orig[1][0] - stitches_orig[0][0],
                               stitches_orig[1][1] - stitches_orig[0][1])
        dist_edit = math.hypot(stitches_edit[1][0] - stitches_edit[0][0],
                               stitches_edit[1][1] - stitches_edit[0][1])
        assert dist_edit < dist_orig

    def test_ajustar_densidade_menos_denso(self):
        p = _pattern_simples()
        result = ajustar_densidade(p, fator=2.0)
        stitches_orig = list(p.stitches)
        stitches_edit = list(result.stitches)
        dist_orig = math.hypot(stitches_orig[1][0] - stitches_orig[0][0],
                               stitches_orig[1][1] - stitches_orig[0][1])
        dist_edit = math.hypot(stitches_edit[1][0] - stitches_edit[0][0],
                               stitches_edit[1][1] - stitches_edit[0][1])
        assert dist_edit > dist_orig

    def test_ajustar_densidade_fator_1(self):
        p = _pattern_simples()
        result = ajustar_densidade(p, fator=1.0)
        # Deve retornar o mesmo padrão
        assert result is p


# ---------------------------------------------------------------------------
# Testes de reordenar_blocos
# ---------------------------------------------------------------------------

class TestReordenarBlocos:
    def test_reordenar_blocos_retorna_pattern(self):
        p = _pattern_multi_cor()
        result = reordenar_blocos(p, nova_ordem=[1, 0])
        assert isinstance(result, pe.EmbPattern)

    def test_reordenar_blocos_ordem_invalida(self):
        p = _pattern_multi_cor()
        with pytest.raises(ValueError, match="fora do range"):
            reordenar_blocos(p, nova_ordem=[5])


# ---------------------------------------------------------------------------
# Testes de inserir_ponto
# ---------------------------------------------------------------------------

class TestInserirPonto:
    def test_inserir_ponto_retorna_pattern(self):
        p = _pattern_simples()
        result = inserir_ponto(p, indice=5, x=2.5, y=0.5)
        assert isinstance(result, pe.EmbPattern)

    def test_inserir_ponto_aumenta_tamanho(self):
        p = _pattern_simples()
        result = inserir_ponto(p, indice=5, x=2.5, y=0.5)
        assert len(list(result.stitches)) == len(list(p.stitches)) + 1

    def test_inserir_ponto_inicio(self):
        p = _pattern_simples()
        result = inserir_ponto(p, indice=0, x=-1.0, y=0.0)
        stitches = list(result.stitches)
        assert stitches[0][0] == -1.0

    def test_inserir_ponto_fim(self):
        p = _pattern_simples()
        result = inserir_ponto(p, indice=-1, x=11.0, y=0.0)
        stitches = list(result.stitches)
        assert stitches[-1][0] == 11.0


# ---------------------------------------------------------------------------
# Testes de remover_ponto
# ---------------------------------------------------------------------------

class TestRemoverPonto:
    def test_remover_ponto_retorna_pattern(self):
        p = _pattern_simples()
        result = remover_ponto(p, indice=5)
        assert isinstance(result, pe.EmbPattern)

    def test_remover_ponto_diminui_tamanho(self):
        p = _pattern_simples()
        result = remover_ponto(p, indice=5)
        assert len(list(result.stitches)) == len(list(p.stitches)) - 1

    def test_remover_ponto_indice_invalido(self):
        p = _pattern_simples()
        with pytest.raises(ValueError, match="fora do range"):
            remover_ponto(p, indice=100)


# ---------------------------------------------------------------------------
# Testes de adicionar_underlay
# ---------------------------------------------------------------------------

class TestAdicionarUnderlay:
    def test_adicionar_underlay_walking(self):
        p = _pattern_simples()
        result = adicionar_underlay(p, tipo="walking")
        assert isinstance(result, pe.EmbPattern)
        # Deve ter mais pontos que o original
        assert len(list(result.stitches)) >= len(list(p.stitches))

    def test_adicionar_underlay_zigzag(self):
        p = _pattern_simples()
        result = adicionar_underlay(p, tipo="zigzag")
        assert isinstance(result, pe.EmbPattern)
        assert len(list(result.stitches)) >= len(list(p.stitches))


# ---------------------------------------------------------------------------
# Testes de remover_underlay
# ---------------------------------------------------------------------------

class TestRemoverUnderlay:
    def test_remover_underlay_retorna_pattern(self):
        p = _pattern_simples()
        result = remover_underlay(p, tolerancia_mm=0.5)
        assert isinstance(result, pe.EmbPattern)

    def test_remover_underlay_pode_diminuir(self):
        """Underlay pode ser removido se detectado."""
        p = _pattern_simples()
        result = remover_underlay(p, tolerancia_mm=10.0)  # tolerância alta
        # Pode ter menos ou igual pontos
        assert len(list(result.stitches)) <= len(list(p.stitches))


# ---------------------------------------------------------------------------
# Testes de aplicar_operacoes
# ---------------------------------------------------------------------------

class TestAplicarOperacoes:
    def test_aplicar_operacoes_compensacao(self):
        p = _pattern_simples()
        caminho = _dst_temporario(p)
        try:
            result = aplicar_operacoes(caminho, [
                {"tipo": "compensacao_pull", "valor_mm": 0.5}
            ])
            assert "pattern" in result
            assert "svg" in result
            assert "stats_original" in result
            assert "stats_editado" in result
            assert "operacoes_aplicadas" in result
            assert result["operacoes_aplicadas"] == ["compensacao_pull"]
        finally:
            os.unlink(caminho)

    def test_aplicar_operacoes_multiplas(self):
        p = _pattern_simples()
        caminho = _dst_temporario(p)
        try:
            result = aplicar_operacoes(caminho, [
                {"tipo": "compensacao_pull", "valor_mm": 0.3},
                {"tipo": "ajustar_densidade", "fator": 0.9},
            ])
            assert len(result["operacoes_aplicadas"]) == 2
        finally:
            os.unlink(caminho)

    def test_aplicar_operacoes_tipo_invalido(self):
        p = _pattern_simples()
        caminho = _dst_temporario(p)
        try:
            with pytest.raises(ValueError, match="desconhecida"):
                aplicar_operacoes(caminho, [
                    {"tipo": "operacao_inexistente"}
                ])
        finally:
            os.unlink(caminho)

    def test_aplicar_operacoes_salva_svg(self):
        p = _pattern_simples()
        caminho = _dst_temporario(p)
        try:
            result = aplicar_operacoes(caminho, [
                {"tipo": "compensacao_pull", "valor_mm": 0.5}
            ])
            assert "<svg" in result["svg"] or "svg" in result["svg"].lower()
        finally:
            os.unlink(caminho)


# ---------------------------------------------------------------------------
# Testes de integração com fixtures
# ---------------------------------------------------------------------------

class TestIntegracaoFixtures:
    def test_limpo_dst(self):
        """Testa operações no fixture limpo.dst."""
        fixture = os.path.join(os.path.dirname(__file__), "fixtures", "limpo.dst")
        if not os.path.exists(fixture):
            pytest.skip("Fixture limpo.dst nao encontrado")

        result = aplicar_operacoes(fixture, [
            {"tipo": "compensacao_pull", "valor_mm": 0.2},
            {"tipo": "ajustar_densidade", "fator": 0.95},
        ])

        assert result["stats_original"]["pontos"] > 0
        assert result["svg"]
