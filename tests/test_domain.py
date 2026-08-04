"""Testes unitários de domain: presets, maquinas e questionario."""
from domain.presets import get_preset, TECIDOS
from domain.maquinas import get_maquina, MAQUINAS, listar_maquinas
from domain.questionario_maquina import (
    PERGUNTAS, validar_respostas, gerar_template_json,
)


# --- presets ---

def test_get_preset_padrao():
    p = get_preset("jeans")
    assert p["variante_usada"] is None
    assert p["compensacao_exigida"] == "media"
    assert p["underlay_exigido"] is False
    assert p["densidade"] == (0.40, 0.50)


def test_get_preset_cetim_ralo():
    p = get_preset("cetim", "ralo")
    assert p["variante_usada"] == "ralo"
    assert p["densidade"] == (0.45, 0.60)
    assert p["underlay_exigido"] is False


def test_get_preset_cetim_padrao():
    p = get_preset("cetim")
    assert p["variante_usada"] == "padrao"


def test_get_preset_cetim_denso():
    p = get_preset("cetim", "denso")
    assert p["variante_usada"] == "denso"
    assert p["densidade"] == (0.35, 0.50)


def test_get_preset_desconhecido_caide_generico():
    p = get_preset("borboleta")
    assert p["variante_usada"] is None
    assert p["densidade"] == TECIDOS["generico"]["densidade"]


def test_get_preset_none_caide_generico():
    p = get_preset(None)
    assert p["variante_usada"] is None


def test_get_preset_underlay_malha():
    p = get_preset("malha")
    assert p["underlay_exigido"] is True


def test_get_preset_variante_invalida_cai_padrao():
    p = get_preset("cetim", "invalido")
    assert p["variante_usada"] == "padrao"


# --- maquinas ---

def test_get_maquina_exata():
    m = get_maquina("tajima-tfmx-6")
    assert m["marca"] == "Tajima"
    assert m["agulhas"] == 6
    assert m["maquina_id"] == "tajima-tfmx-6"


def test_get_maquina_match_parcial():
    m = get_maquina("tajima")
    assert m["maquina_id"].startswith("tajima-tfmx")


def test_get_maquina_desconhecida_caide_generica():
    m = get_maquina("nao_existe")
    assert m["maquina_id"] == "generica"


def test_get_maquina_none_caide_generica():
    m = get_maquina(None)
    assert m["maquina_id"] == "generica"


def test_listar_maquinas_exclui_generica():
    ids = listar_maquinas()
    assert "generica" not in ids
    assert len(ids) >= 10


def test_maquinas_tem_campo_e_trim():
    for mid in MAQUINAS:
        m = get_maquina(mid)
        assert "campo_largura" in m
        assert "campo_altura" in m
        assert "suporta_trim" in m


# --- questionario ---

def test_validar_respostas_vazio_8_erros():
    ok, erros = validar_respostas({})
    assert not ok
    assert len(erros) == 8


def test_validar_respostas_completas_valido():
    resp = {
        "marca": "Teste", "modelo": "M1", "agulhas": 4,
        "formato_nativo": "dst", "campo_largura": 200,
        "campo_altura": 200, "suporta_trim": True,
        "tipo": "domestica",
    }
    ok, erros = validar_respostas(resp)
    assert ok
    assert erros == []


def test_validar_respostas_agulhas_fora_faixa():
    resp = {
        "marca": "T", "modelo": "M", "agulhas": 0,
        "formato_nativo": "dst", "campo_largura": 200,
        "campo_altura": 200, "suporta_trim": True,
        "tipo": "industrial",
    }
    ok, erros = validar_respostas(resp)
    assert not ok
    assert any("agulhas" in e.lower() or "agulha" in e.lower() for e in erros)


def test_gerar_template_json_tem_todos_campos():
    t = gerar_template_json()
    campos = [p["campo"] for p in PERGUNTAS]
    assert set(campos) == set(t.keys())
