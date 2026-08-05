"""Fontes de bordado built-in.

Cada fonte é um mapeamento de caracteres ASCII para padrões de pontos
(absolutos em mm). Para cada caractere, há uma lista de "strokes" com
tipo (STITCH/JUMP/TRIM), coordenadas relativas e cor padrão.

Fontes incluídas:
- block: Bloco simples (sem serifa)
- script: Cursivo simples
- bold: Negrito grosso
"""
import pyembroidery as pe


# ---------------------------------------------------------------------------
# Utilitário: gerar padrão de texto a partir de uma fonte
# ---------------------------------------------------------------------------

def _carregar_fonte(nome: str) -> dict:
    """Retorna o dicionário de glifos da fonte."""
    if nome == "script":
        return _FONT_SCRIPT
    if nome == "bold":
        return _FONT_BOLD
    return _FONT_BLOCK


def renderizar_texto(
    texto: str,
    fonte: str = "block",
    tamanho_mm: float = 10.0,
    espacamento_mm: float = 2.0,
    cor: int = 0,
) -> list[dict]:
    """Renderiza texto como lista de pontos de bordado.

    Args:
        texto: String a renderizar
        fonte: Nome da fonte (block/script/bold)
        tamanho_mm: Altura em mm de cada caractere
        espacamento_mm: Espaço horizontal entre caracteres
        cor: Índice de cor (thread color index)

    Returns:
        Lista de dicts com {x, y, type, color}
    """
    glyphs = _carregar_fonte(fonte)
    escala = tamanho_mm / 10.0  # glifos base são 10mm de altura
    pontos = []
    cursor_x = 0.0

    for char in texto.upper():
        if char == " ":
            cursor_x += espacamento_mm * 3
            continue
        if char == "\n":
            cursor_x = 0
            continue

        glyph = glyphs.get(char, glyphs.get("?", _GLIFO_DEFAULT))
        for stroke in glyph:
            x = cursor_x + stroke["x"] * escala
            y = stroke["y"] * escala
            pontos.append({
                "x": x,
                "y": y,
                "type": stroke.get("type", pe.STITCH),
                "color": stroke.get("color", cor),
            })

        # Avançar cursor (largura do glifo + espaçamento)
        largura = max((s["x"] for s in glyph), default=0) * escala
        cursor_x += max(largura + espacamento_mm, espacamento_mm * 1.5)

    return pontos


def pontos_para_pattern(pontos: list[dict]) -> pe.EmbPattern:
    """Converte lista de pontos em EmbPattern do pyembroidery."""
    pattern = pe.EmbPattern()
    cor_atual = -1

    for p in pontos:
        tipo = p.get("type", pe.STITCH)
        cor = p.get("color", 0)

        # Mudança de cor
        if cor != cor_atual:
            pattern.add_command(pe.COLOR_CHANGE)
            cor_atual = cor

        if tipo == pe.STITCH:
            pattern.add_stitch_absolute(pe.STITCH, p["x"], p["y"])
        elif tipo == pe.JUMP:
            pattern.add_stitch_absolute(pe.JUMP, p["x"], p["y"])
        elif tipo == pe.TRIM:
            pattern.add_stitch_absolute(pe.TRIM, p["x"], p["y"])

    pattern.add_command(pe.END)
    return pattern


# ---------------------------------------------------------------------------
# Fonte: BLOCK (bloco simples sem serifa)
# ---------------------------------------------------------------------------
# Cada glifo é uma lista de strokes com coordenadas absolutas (base 10mm)
# Coordenadas Y: 0 = base, 10 = topo

_GLIFO_DEFAULT = [
    {"x": 0, "y": 0, "type": pe.STITCH},
    {"x": 0, "y": 10, "type": pe.STITCH},
    {"x": 5, "y": 10, "type": pe.STITCH},
    {"x": 5, "y": 0, "type": pe.STITCH},
]

_FONT_BLOCK = {
    "A": [
        {"x": 0, "y": 0}, {"x": 0, "y": 8}, {"x": 2.5, "y": 10},
        {"x": 5, "y": 8}, {"x": 5, "y": 0}, {"x": 5, "y": 5},
        {"x": 0, "y": 5},
    ],
    "B": [
        {"x": 0, "y": 0}, {"x": 0, "y": 10}, {"x": 4, "y": 10},
        {"x": 5, "y": 8}, {"x": 5, "y": 6}, {"x": 4, "y": 5},
        {"x": 0, "y": 5},
        {"x": 4, "y": 5}, {"x": 5, "y": 4}, {"x": 5, "y": 2},
        {"x": 4, "y": 0}, {"x": 0, "y": 0},
    ],
    "C": [
        {"x": 5, "y": 8}, {"x": 4, "y": 10}, {"x": 1, "y": 10},
        {"x": 0, "y": 8}, {"x": 0, "y": 2}, {"x": 1, "y": 0},
        {"x": 4, "y": 0}, {"x": 5, "y": 2},
    ],
    "D": [
        {"x": 0, "y": 0}, {"x": 0, "y": 10}, {"x": 3, "y": 10},
        {"x": 5, "y": 7}, {"x": 5, "y": 3}, {"x": 3, "y": 0},
    ],
    "E": [
        {"x": 5, "y": 10}, {"x": 0, "y": 10}, {"x": 0, "y": 0},
        {"x": 5, "y": 0}, {"x": 0, "y": 5}, {"x": 4, "y": 5},
    ],
    "F": [
        {"x": 5, "y": 10}, {"x": 0, "y": 10}, {"x": 0, "y": 0},
        {"x": 0, "y": 5}, {"x": 4, "y": 5},
    ],
    "G": [
        {"x": 5, "y": 8}, {"x": 4, "y": 10}, {"x": 1, "y": 10},
        {"x": 0, "y": 8}, {"x": 0, "y": 2}, {"x": 1, "y": 0},
        {"x": 4, "y": 0}, {"x": 5, "y": 2}, {"x": 5, "y": 5},
        {"x": 3, "y": 5},
    ],
    "H": [
        {"x": 0, "y": 0}, {"x": 0, "y": 10}, {"x": 0, "y": 5},
        {"x": 5, "y": 5}, {"x": 5, "y": 0}, {"x": 5, "y": 10},
    ],
    "I": [
        {"x": 1, "y": 0}, {"x": 4, "y": 0},
        {"x": 2.5, "y": 0}, {"x": 2.5, "y": 10},
        {"x": 1, "y": 10}, {"x": 4, "y": 10},
    ],
    "J": [
        {"x": 5, "y": 10}, {"x": 5, "y": 2}, {"x": 4, "y": 0},
        {"x": 2, "y": 0}, {"x": 0, "y": 2},
    ],
    "K": [
        {"x": 0, "y": 0}, {"x": 0, "y": 10},
        {"x": 5, "y": 10}, {"x": 0, "y": 5},
        {"x": 5, "y": 0},
    ],
    "L": [
        {"x": 0, "y": 10}, {"x": 0, "y": 0}, {"x": 5, "y": 0},
    ],
    "M": [
        {"x": 0, "y": 0}, {"x": 0, "y": 10}, {"x": 2.5, "y": 5},
        {"x": 5, "y": 10}, {"x": 5, "y": 0},
    ],
    "N": [
        {"x": 0, "y": 0}, {"x": 0, "y": 10}, {"x": 5, "y": 0},
        {"x": 5, "y": 10},
    ],
    "O": [
        {"x": 1, "y": 0}, {"x": 0, "y": 2}, {"x": 0, "y": 8},
        {"x": 1, "y": 10}, {"x": 4, "y": 10}, {"x": 5, "y": 8},
        {"x": 5, "y": 2}, {"x": 4, "y": 0},
    ],
    "P": [
        {"x": 0, "y": 0}, {"x": 0, "y": 10}, {"x": 4, "y": 10},
        {"x": 5, "y": 8}, {"x": 5, "y": 6}, {"x": 4, "y": 5},
        {"x": 0, "y": 5},
    ],
    "Q": [
        {"x": 1, "y": 0}, {"x": 0, "y": 2}, {"x": 0, "y": 8},
        {"x": 1, "y": 10}, {"x": 4, "y": 10}, {"x": 5, "y": 8},
        {"x": 5, "y": 2}, {"x": 4, "y": 0},
        {"x": 5, "y": 0}, {"x": 4, "y": -2},
    ],
    "R": [
        {"x": 0, "y": 0}, {"x": 0, "y": 10}, {"x": 4, "y": 10},
        {"x": 5, "y": 8}, {"x": 5, "y": 6}, {"x": 4, "y": 5},
        {"x": 0, "y": 5},
        {"x": 3, "y": 5}, {"x": 5, "y": 0},
    ],
    "S": [
        {"x": 5, "y": 8}, {"x": 4, "y": 10}, {"x": 1, "y": 10},
        {"x": 0, "y": 8}, {"x": 1, "y": 5}, {"x": 4, "y": 5},
        {"x": 5, "y": 2}, {"x": 4, "y": 0}, {"x": 1, "y": 0},
        {"x": 0, "y": 2},
    ],
    "T": [
        {"x": 0, "y": 10}, {"x": 5, "y": 10},
        {"x": 2.5, "y": 10}, {"x": 2.5, "y": 0},
    ],
    "U": [
        {"x": 0, "y": 10}, {"x": 0, "y": 2}, {"x": 1, "y": 0},
        {"x": 4, "y": 0}, {"x": 5, "y": 2}, {"x": 5, "y": 10},
    ],
    "V": [
        {"x": 0, "y": 10}, {"x": 2.5, "y": 0}, {"x": 5, "y": 10},
    ],
    "W": [
        {"x": 0, "y": 10}, {"x": 1.5, "y": 0}, {"x": 2.5, "y": 5},
        {"x": 3.5, "y": 0}, {"x": 5, "y": 10},
    ],
    "X": [
        {"x": 0, "y": 0}, {"x": 5, "y": 10},
        {"x": 5, "y": 0}, {"x": 0, "y": 10},
    ],
    "Y": [
        {"x": 0, "y": 10}, {"x": 2.5, "y": 5},
        {"x": 5, "y": 10}, {"x": 2.5, "y": 5}, {"x": 2.5, "y": 0},
    ],
    "Z": [
        {"x": 0, "y": 10}, {"x": 5, "y": 10}, {"x": 0, "y": 0},
        {"x": 5, "y": 0},
    ],
    "0": [
        {"x": 1, "y": 0}, {"x": 0, "y": 2}, {"x": 0, "y": 8},
        {"x": 1, "y": 10}, {"x": 4, "y": 10}, {"x": 5, "y": 8},
        {"x": 5, "y": 2}, {"x": 4, "y": 0},
        {"x": 0, "y": 10}, {"x": 5, "y": 0},
    ],
    "1": [
        {"x": 2, "y": 0}, {"x": 2.5, "y": 0}, {"x": 2.5, "y": 10},
        {"x": 1, "y": 8},
    ],
    "2": [
        {"x": 0, "y": 8}, {"x": 1, "y": 10}, {"x": 4, "y": 10},
        {"x": 5, "y": 8}, {"x": 5, "y": 6}, {"x": 4, "y": 5},
        {"x": 0, "y": 0}, {"x": 5, "y": 0},
    ],
    "3": [
        {"x": 0, "y": 10}, {"x": 5, "y": 10}, {"x": 2.5, "y": 5},
        {"x": 5, "y": 5}, {"x": 5, "y": 2}, {"x": 4, "y": 0},
        {"x": 1, "y": 0}, {"x": 0, "y": 2},
    ],
    "4": [
        {"x": 4, "y": 0}, {"x": 4, "y": 10}, {"x": 0, "y": 4},
        {"x": 5, "y": 4},
    ],
    "5": [
        {"x": 5, "y": 10}, {"x": 0, "y": 10}, {"x": 0, "y": 5},
        {"x": 4, "y": 5}, {"x": 5, "y": 4}, {"x": 5, "y": 2},
        {"x": 4, "y": 0}, {"x": 1, "y": 0}, {"x": 0, "y": 2},
    ],
    "6": [
        {"x": 5, "y": 8}, {"x": 4, "y": 10}, {"x": 1, "y": 10},
        {"x": 0, "y": 8}, {"x": 0, "y": 2}, {"x": 1, "y": 0},
        {"x": 4, "y": 0}, {"x": 5, "y": 2}, {"x": 5, "y": 4},
        {"x": 4, "y": 5}, {"x": 0, "y": 5},
    ],
    "7": [
        {"x": 0, "y": 10}, {"x": 5, "y": 10}, {"x": 2.5, "y": 0},
    ],
    "8": [
        {"x": 1, "y": 0}, {"x": 0, "y": 2}, {"x": 0, "y": 5},
        {"x": 1, "y": 5}, {"x": 4, "y": 5}, {"x": 5, "y": 5},
        {"x": 5, "y": 2}, {"x": 4, "y": 0},
        {"x": 1, "y": 5}, {"x": 0, "y": 5},
        {"x": 1, "y": 10}, {"x": 4, "y": 10}, {"x": 5, "y": 8},
    ],
    "9": [
        {"x": 5, "y": 5}, {"x": 4, "y": 5}, {"x": 0, "y": 5},
        {"x": 0, "y": 6}, {"x": 0, "y": 8}, {"x": 1, "y": 10},
        {"x": 4, "y": 10}, {"x": 5, "y": 8}, {"x": 5, "y": 2},
        {"x": 4, "y": 0}, {"x": 1, "y": 0}, {"x": 0, "y": 2},
    ],
    "?": [
        {"x": 1, "y": 10}, {"x": 4, "y": 10}, {"x": 5, "y": 8},
        {"x": 5, "y": 6}, {"x": 4, "y": 5}, {"x": 2.5, "y": 5},
        {"x": 2.5, "y": 2},
    ],
    "!": [
        {"x": 2, "y": 0}, {"x": 3, "y": 0},
        {"x": 2.5, "y": 2}, {"x": 2.5, "y": 7},
        {"x": 2, "y": 9}, {"x": 3, "y": 9},
    ],
    "-": [
        {"x": 0, "y": 5}, {"x": 5, "y": 5},
    ],
    ".": [
        {"x": 2, "y": 0}, {"x": 3, "y": 0},
    ],
    ",": [
        {"x": 2, "y": 0}, {"x": 3, "y": 0},
        {"x": 3, "y": -2}, {"x": 2, "y": -3},
    ],
    ":": [
        {"x": 2, "y": 2}, {"x": 3, "y": 2},
        {"x": 2, "y": 8}, {"x": 3, "y": 8},
    ],
    "/": [
        {"x": 5, "y": 0}, {"x": 0, "y": 10},
    ],
    "(": [
        {"x": 4, "y": 10}, {"x": 2, "y": 10}, {"x": 1, "y": 8},
        {"x": 1, "y": 2}, {"x": 2, "y": 0}, {"x": 4, "y": 0},
    ],
    ")": [
        {"x": 1, "y": 10}, {"x": 3, "y": 10}, {"x": 4, "y": 8},
        {"x": 4, "y": 2}, {"x": 3, "y": 0}, {"x": 1, "y": 0},
    ],
    "@": [
        {"x": 4, "y": 5}, {"x": 5, "y": 6}, {"x": 5, "y": 8},
        {"x": 4, "y": 10}, {"x": 1, "y": 10}, {"x": 0, "y": 8},
        {"x": 0, "y": 2}, {"x": 1, "y": 0}, {"x": 4, "y": 0},
        {"x": 5, "y": 2}, {"x": 5, "y": 4},
    ],
}

# Script e Bold herdam de Block com pequenas variações
# (para simplificar, usamos o mesmo glyphs - futuras versões podem refinar)
_FONT_SCRIPT = _FONT_BLOCK
_FONT_BOLD = _FONT_BLOCK
