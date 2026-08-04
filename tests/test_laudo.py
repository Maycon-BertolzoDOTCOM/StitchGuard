"""Testes do módulo de laudo técnico."""
import os
import tempfile

from laudo.gerador import (
    gerar_laudo_html,
    salvar_laudo,
    gerar_laudo,
    _cor_score,
    _status_texto,
)


def _resultado_exemplo():
    """Retorna resultado de exemplo para testes."""
    return {
        "score_global": 0.91,
        "aprovado": True,
        "resumo": {
            "pontos": 1234,
            "passo_medio_mm": 0.42,
            "maior_salto_mm": 3.2,
            "largura_mm": 25.5,
            "altura_mm": 18.3,
        },
        "itens": {
            "tipo_tecido": {"score": 1.0, "aprovado": True, "detalhe": "Tecido 'jeans' reconhecido."},
            "compensacao": {"score": 1.0, "aprovado": True, "detalhe": "Compensacao media correta para jeans."},
            "amarracao": {"score": 1.0, "aprovado": True, "detalhe": "Underlay ausente correto para jeans."},
            "densidade": {"score": 0.3, "aprovado": False, "detalhe": "Passo medio 0.60mm fora de [0.40, 0.50]."},
            "saltos": {"score": 1.0, "aprovado": True, "detalhe": "Maior salto 3.2mm < 5.0mm."},
            "ordem_costura": {"score": None, "aprovado": False, "detalhe": "Requer analise visual."},
            "angulos_satin": {"score": None, "aprovado": False, "detalhe": "Requer analise visual."},
            "nos_lock": {"score": 1.0, "aprovado": True, "detalhe": "2 paradas detectadas."},
            "limite_pontos": {"score": 1.0, "aprovado": True, "detalhe": "1234 pontos dentro do limite."},
            "limite_cores": {"score": None, "aprovado": True, "detalhe": "Maquina nao informada."},
            "cabe_no_aro": {"score": None, "aprovado": True, "detalhe": "Maquina nao informada."},
        },
    }


class TestCorScore:
    def test_verde(self):
        assert _cor_score(1.0) == "#10B981"

    def test_amarelo(self):
        assert _cor_score(0.5) == "#F59E0B"

    def test_vermelho(self):
        assert _cor_score(0.0) == "#EF4444"

    def test_none(self):
        assert _cor_score(None) == "#9CA3AF"


class TestStatusTexto:
    def test_aprovado(self):
        assert _status_texto(1.0) == "Aprovado"

    def test_atencao(self):
        assert _status_texto(0.5) == "Atenção"

    def test_reprovado(self):
        assert _status_texto(0.0) == "Reprovado"

    def test_pendente(self):
        assert _status_texto(None) == "Pendente"


class TestGerarLaudoHtml:
    def test_retorna_html(self):
        resultado = _resultado_exemplo()
        html = gerar_laudo_html("test123", resultado)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_contem_job_id(self):
        resultado = _resultado_exemplo()
        html = gerar_laudo_html("test123", resultado)
        assert "test123" in html

    def test_contem_score_global(self):
        resultado = _resultado_exemplo()
        html = gerar_laudo_html("test123", resultado)
        assert "0.91" in html

    def test_contem_checklist(self):
        resultado = _resultado_exemplo()
        html = gerar_laudo_html("test123", resultado)
        assert "tipo_tecido" in html
        assert "compensacao" in html

    def test_contem_estatisticas(self):
        resultado = _resultado_exemplo()
        html = gerar_laudo_html("test123", resultado)
        assert "1234" in html
        assert "25.5" in html

    def test_aprovado(self):
        resultado = _resultado_exemplo()
        html = gerar_laudo_html("test123", resultado)
        assert "APROVADO" in html

    def test_reprovado(self):
        resultado = _resultado_exemplo()
        resultado["aprovado"] = False
        html = gerar_laudo_html("test123", resultado)
        assert "REPROVADO" in html

    def test_com_operacoes_edicao(self):
        resultado = _resultado_exemplo()
        html = gerar_laudo_html(
            "test123",
            resultado,
            operacoes_edicao=["compensacao_pull", "ajustar_densidade"],
        )
        assert "Edição Aplicada" in html
        assert "compensacao_pull" in html

    def test_com_stats_editado(self):
        resultado = _resultado_exemplo()
        html = gerar_laudo_html(
            "test123",
            resultado,
            operacoes_edicao=["compensacao_pull"],
            stats_editado={"pontos": 1100, "largura_mm": 24.0, "altura_mm": 17.0},
        )
        assert "1100" in html

    def test_recomendacoes(self):
        resultado = _resultado_exemplo()
        resultado["aprovado"] = False
        html = gerar_laudo_html("test123", resultado)
        assert "Recomendações" in html


class TestSalvarLaudo:
    def test_salva_arquivo(self):
        resultado = _resultado_exemplo()
        html = gerar_laudo_html("test123", resultado)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            caminho = f.name
        try:
            salvar_laudo(html, caminho)
            assert os.path.exists(caminho)
            with open(caminho, "r", encoding="utf-8") as f:
                conteudo = f.read()
            assert "test123" in conteudo
        finally:
            os.unlink(caminho)


class TestGerarLaudo:
    def test_gera_e_salva(self):
        resultado = _resultado_exemplo()
        caminho = gerar_laudo("test123", resultado)
        try:
            assert os.path.exists(caminho)
            assert caminho.endswith(".html")
        finally:
            os.unlink(caminho)

    def test_gera_com_caminho_customizado(self):
        resultado = _resultado_exemplo()
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            caminho_custom = f.name
        try:
            caminho = gerar_laudo("test123", resultado, caminho_saida=caminho_custom)
            assert caminho == caminho_custom
            assert os.path.exists(caminho)
        finally:
            os.unlink(caminho)
