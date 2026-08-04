"""StitchGuard - núcleo de digitalização programática (MVP).

Converte o JSON de arte (formas geométricas em mm) em uma sequência de
pontos de bordado via pyembroidery, respeitando os presets de tecido
(domain/presets.py): densidade, compensação e underlay.

Convenção: neste pipeline 1 unidade pyembroidery == 1 mm (sem escala).
"""
import math

import pyembroidery as pe

# Constantes do underlay (running stitch de contorno)
UNDERLAY_PASSO_MM = 0.8        # passo do contorno (mais largo que o fill)
UNDERLAY_INSET_MM = 1.0        # deslocamento do contorno para dentro da forma
UNDERLAY_ZIGZAG_AMPLITUDE_MM = 1.5

# Compensação aplicada por nível (expande a forma antes de preencher)
COMPENSACAO_MM = {"alta": 0.8, "media": 0.5, "baixa": 0.3}


def _densidade_passo_mm(preset):
    """Passo de preenchimento = ponto médio da faixa de densidade do preset."""
    lo, hi = preset["densidade"]
    return round((lo + hi) / 2.0, 2)


def _lock_stitch(pattern, x, y, n=3):
    """Pequena amarração (lock stitch) — 3 pontinhos reversos de 0.5mm."""
    for _ in range(n):
        pattern.add_stitch_absolute(pe.STITCH, x + 0.5, y)
        pattern.add_stitch_absolute(pe.STITCH, x, y)


def _preencher_retangulo(pattern, forma, passo, comp_x, comp_y):
    """Preenche um retângulo em colunas verticais (serpentina)."""
    x0, y0 = forma["x"], forma["y"]
    x1 = x0 + forma["largura"] + 2 * comp_x
    y1 = y0 + forma["altura"] + 2 * comp_y
    x0 -= comp_x
    y0 -= comp_y
    col = x0
    descendo = True
    while col <= x1 + passo:
        if descendo:
            ys = range(0, int((y1 - y0) / passo) + 1)
            for i in ys:
                pattern.add_stitch_absolute(pe.STITCH, col, y0 + i * passo)
        else:
            ys = range(int((y1 - y0) / passo), -1, -1)
            for i in ys:
                pattern.add_stitch_absolute(pe.STITCH, col, y0 + i * passo)
        col += passo
        descendo = not descendo


def _preencher_circulo(pattern, forma, passo, comp):
    """Preenche um círculo por colunas verticais (serpentina)."""
    cx, cy = forma["centro_x"], forma["centro_y"]
    r = forma["raio"] + comp
    col = cx - r
    descendo = True
    while col <= cx + r + passo:
        dx = col - cx
        semi = math.sqrt(max(0.0, r * r - dx * dx))
        if descendo:
            ys = range(0, int((2 * semi) / passo) + 1)
            for i in ys:
                pattern.add_stitch_absolute(pe.STITCH, col, cy - semi + i * passo)
        else:
            ys = range(int((2 * semi) / passo), -1, -1)
            for i in ys:
                pattern.add_stitch_absolute(pe.STITCH, col, cy - semi + i * passo)
        col += passo
        descendo = not descendo


def _preencher_poligono(pattern, forma, passo, comp):
    """Preenche um polígono por scanline horizontal (serpentina)."""
    pts = [(p[0], p[1]) for p in forma["pontos"]]
    x0 = min(p[0] for p in pts) - comp
    x1 = max(p[0] for p in pts) + comp
    y0 = min(p[1] for p in pts) - comp
    y1 = max(p[1] for p in pts) + comp
    linha = y0
    direita = True
    while linha <= y1 + passo:
        inter = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            if (a[1] <= linha <= b[1]) or (b[1] <= linha <= a[1]):
                if abs(b[1] - a[1]) < 1e-9:
                    continue
                t = (linha - a[1]) / (b[1] - a[1])
                inter.append(a[0] + t * (b[0] - a[0]))
        inter.sort()
        for i in range(0, len(inter) - 1, 2):
            lo, hi = max(inter[i], x0), min(inter[i + 1], x1)
            xs = range(0, int((hi - lo) / passo) + 1)
            if not direita:
                xs = reversed(list(xs))
            for j in xs:
                pattern.add_stitch_absolute(pe.STITCH, lo + j * passo, linha)
        linha += passo
        direita = not direita


def _underlay_contorno(pattern, forma):
    """Running stitch de contorno (inset para dentro), passo mais largo."""
    inset = UNDERLAY_INSET_MM
    passo = UNDERLAY_PASSO_MM

    def _traco(a, b):
        dist = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(dist / passo))
        for i in range(1, n + 1):
            t = i / n
            pattern.add_stitch_absolute(pe.STITCH, a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))

    if forma["tipo"] == "retangulo":
        x0, y0 = forma["x"] + inset, forma["y"] + inset
        x1 = x0 + forma["largura"] - 2 * inset
        y1 = y0 + forma["altura"] - 2 * inset
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for i in range(4):
            _traco(pts[i], pts[(i + 1) % 4])
    elif forma["tipo"] == "circulo":
        cx, cy = forma["centro_x"], forma["centro_y"]
        r = forma["raio"] - inset
        if r <= 0:
            return
        n = max(8, int(2 * math.pi * r / passo))
        for i in range(n):
            a0 = 2 * math.pi * i / n
            a1 = 2 * math.pi * (i + 1) / n
            _traco((cx + r * math.cos(a0), cy + r * math.sin(a0)),
                   (cx + r * math.cos(a1), cy + r * math.sin(a1)))


def _underlay_zigzag(pattern, forma):
    """Zig-zag central para formas largas (>15mm) — estabilização opcional."""
    if forma["tipo"] != "retangulo":
        return
    largura = forma["largura"]
    if largura <= 15.0:
        return
    cy = forma["y"] + forma["altura"] / 2.0
    amp = UNDERLAY_ZIGZAG_AMPLITUDE_MM
    x = forma["x"]
    passo = UNDERLAY_PASSO_MM
    passo_x = passo / 2.0
    alterna = True
    while x <= forma["x"] + largura + passo_x:
        dy = amp if alterna else -amp
        pattern.add_stitch_absolute(pe.STITCH, x, cy + dy)
        x += passo_x
        alterna = not alterna


def rastrear_bloco(pattern, forma, preset):
    """Adiciona os pontos de um bloco (forma) ao pattern, conforme o preset.

    Ordem: lock inicial -> (underlay contorno + zigzag) -> fill principal.

    Args:
        pattern: pyembroidery.EmbPattern em construção.
        forma: dict do JSON de arte (tipo, x/y, largura/altura, ...).
        preset: dict resolvido por domain.presets.get_preset().

    Returns:
        Número de pontos adicionados (lock inicial + fill + underlay).
    """
    comp = COMPENSACAO_MM.get(preset["compensacao_exigida"], 0.0) if preset["compensacao_exigida"] else 0.0
    passo = _densidade_passo_mm(preset)
    contados = 0
    lock_x = forma.get("x", forma.get("centro_x", 0.0))
    lock_y = forma.get("y", forma.get("centro_y", 0.0))
    _lock_stitch(pattern, lock_x, lock_y)
    contados += 3

    if preset["underlay_exigido"]:
        _underlay_contorno(pattern, forma)
        _underlay_zigzag(pattern, forma)

    if forma["tipo"] == "retangulo":
        _preencher_retangulo(pattern, forma, passo, comp, comp)
    elif forma["tipo"] == "circulo":
        _preencher_circulo(pattern, forma, passo, comp)
    elif forma["tipo"] == "poligono":
        _preencher_poligono(pattern, forma, passo, comp)
    else:
        raise ValueError(f"Tipo de forma desconhecido: {forma['tipo']}")
    return contados
