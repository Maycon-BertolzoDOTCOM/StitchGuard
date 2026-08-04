"""Processamento de imagens — conversao SVG/PNG para stitches."""
import math
import re
import xml.etree.ElementTree as ET

import pyembroidery as pe
from PIL import Image


def parse_svg_path(d: str) -> list[tuple[str, list[float]]]:
    """Parse de atributo 'd' de path SVG em comandos.

    Retorna lista de (comando, [args]).
    Ex: 'M 0 0 L 10 10' -> [('M', [0, 0]), ('L', [10, 10])]
    """
    commands = []
    # Tokenizar: separar comandos de numeros
    tokens = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', d)
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha():
            cmd = tok
            args = []
            i += 1
            while i < len(tokens) and not tokens[i].isalpha():
                args.append(float(tokens[i]))
                i += 1
            commands.append((cmd, args))
        else:
            i += 1
    return commands


def svg_path_to_points(d: str, scale: float = 1.0) -> list[tuple[float, float]]:
    """Converte atributo 'd' de SVG path em lista de pontos (x, y).

    Suporta: M, L, H, V, C, S, Q, T, Z.
    Curvas C/S/Q/T sao aproximadas com linhas (N segmentos).
    """
    commands = parse_svg_path(d)
    points = []
    cx, cy = 0.0, 0.0  # cursor atual
    sx, sy = 0.0, 0.0  # start do subpath
    qx, qy = 0.0, 0.0  # ultimo controle quadratico
    last_cmd = ""
    N_CURVE_SEGS = 8  # segmentos para aproximar curvas

    for cmd, args in commands:
        c = cmd.lower()
        is_rel = cmd.islower()

        if c == "m":
            for j in range(0, len(args), 2):
                x, y = args[j], args[j + 1]
                if is_rel:
                    x += cx
                    y += cy
                cx, cy = x, y
                if j == 0:
                    sx, sy = x, y
                points.append((x * scale, y * scale))
        elif c == "l":
            for j in range(0, len(args), 2):
                x, y = args[j], args[j + 1]
                if is_rel:
                    x += cx
                    y += cy
                cx, cy = x, y
                points.append((x * scale, y * scale))
        elif c == "h":
            for val in args:
                x = val + cx if is_rel else val
                cx = x
                points.append((x * scale, cy * scale))
        elif c == "v":
            for val in args:
                y = val + cy if is_rel else val
                cy = y
                points.append((cx * scale, y * scale))
        elif c == "c":
            for j in range(0, len(args), 6):
                x1 = args[j] + (cx if is_rel else 0)
                y1 = args[j + 1] + (cy if is_rel else 0)
                x2 = args[j + 2] + (cx if is_rel else 0)
                y2 = args[j + 3] + (cy if is_rel else 0)
                x = args[j + 4] + (cx if is_rel else 0)
                y = args[j + 5] + (cy if is_rel else 0)
                # Aproximar curva cubica com linhas
                for k in range(1, N_CURVE_SEGS + 1):
                    t = k / N_CURVE_SEGS
                    t2 = t * t
                    t3 = t2 * t
                    mt = 1 - t
                    mt2 = mt * mt
                    mt3 = mt2 * mt
                    px = mt3 * cx + 3 * mt2 * t * x1 + 3 * mt * t2 * x2 + t3 * x
                    py = mt3 * cy + 3 * mt2 * t * y1 + 3 * mt * t2 * y2 + t3 * y
                    points.append((px * scale, py * scale))
                cx, cy = x, y
        elif c == "s":
            for j in range(0, len(args), 4):
                x2 = args[j] + (cx if is_rel else 0)
                y2 = args[j + 1] + (cy if is_rel else 0)
                x = args[j + 2] + (cx if is_rel else 0)
                y = args[j + 3] + (cy if is_rel else 0)
                x1 = 2 * cx - qx if last_cmd.lower() in ("c", "s") else cx
                y1 = 2 * cy - qy if last_cmd.lower() in ("c", "s") else cy
                for k in range(1, N_CURVE_SEGS + 1):
                    t = k / N_CURVE_SEGS
                    t2 = t * t
                    t3 = t2 * t
                    mt = 1 - t
                    mt2 = mt * mt
                    mt3 = mt2 * mt
                    px = mt3 * cx + 3 * mt2 * t * x1 + 3 * mt * t2 * x2 + t3 * x
                    py = mt3 * cy + 3 * mt2 * t * y1 + 3 * mt * t2 * y2 + t3 * y
                    points.append((px * scale, py * scale))
                qx, qy = x2, y2
                cx, cy = x, y
        elif c == "q":
            for j in range(0, len(args), 4):
                qx = args[j] + (cx if is_rel else 0)
                qy = args[j + 1] + (cy if is_rel else 0)
                x = args[j + 2] + (cx if is_rel else 0)
                y = args[j + 3] + (cy if is_rel else 0)
                for k in range(1, N_CURVE_SEGS + 1):
                    t = k / N_CURVE_SEGS
                    mt = 1 - t
                    px = mt * mt * cx + 2 * mt * t * qx + t * t * x
                    py = mt * mt * cy + 2 * mt * t * qy + t * t * y
                    points.append((px * scale, py * scale))
                cx, cy = x, y
        elif c == "t":
            for j in range(0, len(args), 2):
                x = args[j] + (cx if is_rel else 0)
                y = args[j + 1] + (cy if is_rel else 0)
                qx = 2 * cx - qx
                qy = 2 * cy - qy
                for k in range(1, N_CURVE_SEGS + 1):
                    t = k / N_CURVE_SEGS
                    mt = 1 - t
                    px = mt * mt * cx + 2 * mt * t * qx + t * t * x
                    py = mt * mt * cy + 2 * mt * t * qy + t * t * y
                    points.append((px * scale, py * scale))
                cx, cy = x, y
        elif c == "z":
            cx, cy = sx, sy
            points.append((sx * scale, sy * scale))

        last_cmd = cmd

    return points


def svg_para_pattern(svg_path: str, step_mm: float = 0.4) -> pe.EmbPattern:
    """Le SVG e converte para EmbPattern com stitches.

    Cada path vira um bloco de costura (STITCH).
    Saltos entre paths sao inseridos (JUMP).
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Namespace SVG
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Obter viewBox ou width/height para escala
    viewBox = root.get("viewBox")
    if viewBox:
        parts = viewBox.split()
        vb_x, vb_y, vb_w, vb_h = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
    else:
        vb_x, vb_y = 0, 0
        vb_w = float(root.get("width", "100").replace("mm", "").replace("px", ""))
        vb_h = float(root.get("height", "100").replace("mm", "").replace("px", ""))

    # Escala: SVG usa pixels, embroidery usa mm (1 unidade = 1mm)
    # Normalizar para caber em ~10mm (tamanho de preview)
    scale = 10.0 / max(vb_w, vb_h) if max(vb_w, vb_h) > 0 else 1.0

    pattern = pe.EmbPattern()
    pattern.add_thread(pe.EmbThread(0x000000))  # preto padrao

    paths = root.findall(".//svg:path", ns)
    if not paths:
        paths = root.findall(".//{http://www.w3.org/2000/svg}path")

    first_path = True
    for path_elem in paths:
        d = path_elem.get("d", "")
        if not d:
            continue

        points = svg_path_to_points(d, scale)
        if not points:
            continue

        # Converter cor do path
        style = path_elem.get("style", "")
        fill = ""
        for part in style.split(";"):
            if part.strip().startswith("fill:"):
                fill = part.split(":", 1)[1].strip()
            elif part.strip().startswith("stroke:"):
                stroke = part.split(":", 1)[1].strip()
                if stroke and stroke != "none":
                    fill = stroke

        if not fill or fill == "none":
            fill = path_elem.get("fill", "#000000")
            if fill == "none":
                fill = "#000000"

        # Converter cor hex para int
        try:
            if fill.startswith("#"):
                color = int(fill[1:16], 16)
            else:
                color = 0x000000
        except ValueError:
            color = 0x000000

        # Adicionar thread se cor diferente
        if pattern.threadlist and color != pattern.threadlist[0].color:
            pattern.add_thread(pe.EmbThread(color))

        # JUMP entre paths (se nao e o primeiro)
        if not first_path and points:
            last_stitch = pattern.stitches[-1] if pattern.stitches else [0, 0, 0]
            pattern.add_stitch_absolute(pe.JUMP, last_stitch[0], last_stitch[1])
        first_path = False

        # Adicionar stitches
        for i, (x, y) in enumerate(points):
            if i == 0:
                pattern.add_stitch_absolute(pe.STITCH, x, y)
            else:
                # Inserir saltos intermediarios se distancia > 5mm
                prev_x, prev_y = points[i - 1]
                dist = math.sqrt((x - prev_x) ** 2 + (y - prev_y) ** 2)
                if dist > 5.0:
                    pattern.add_stitch_absolute(pe.JUMP, x, y)
                else:
                    pattern.add_stitch_absolute(pe.STITCH, x, y)

    return pattern


def png_para_pattern(png_path: str, threshold: int = 128, step_mm: float = 0.5) -> pe.EmbPattern:
    """Le PNG, extrai silhueta (edge detection) e converte para EmbPattern.

    1. Converte para escala de cinza
    2. Aplica threshold para binarizar
    3. Extrai contornos (simplificado: borda preta)
    4. Converte borda para stitches
    """
    img = Image.open(png_path)

    # Converter para escala de cinza
    if img.mode != "L":
        img = img.convert("L")

    # Redimensionar para tamanho razoavel (max 200px)
    max_dim = max(img.size)
    if max_dim > 200:
        ratio = 200 / max_dim
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

    # Binarizar
    width, height = img.size
    pixels = img.load()

    # Extrair bordas (simplificado: pixels pretos proximos a pixels brancos)
    borda = []
    for y in range(height):
        for x in range(width):
            if pixels[x, y] < threshold:
                # Verificar se e borda (tem vizinho branco)
                is_borda = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if pixels[nx, ny] >= threshold:
                            is_borda = True
                            break
                if is_borda:
                    borda.append((x, y))

    if not borda:
        borda = [(x, y) for y in range(height) for x in range(width) if pixels[x, y] < threshold]

    if not borda:
        return pe.EmbPattern()

    # Escala para mm (1 pixel = 1mm, normalizar para ~10mm)
    scale = 10.0 / max(width, height) if max(width, height) > 0 else 1.0

    pattern = pe.EmbPattern()
    pattern.add_thread(pe.EmbThread(0x000000))

    # Ordenar borda por proximidade (travelling salesman simplificado)
    if borda:
        ordered = [borda[0]]
        remaining = set(borda[1:])
        while remaining:
            last = ordered[-1]
            nearest = min(remaining, key=lambda p: (p[0] - last[0]) ** 2 + (p[1] - last[1]) ** 2)
            ordered.append(nearest)
            remaining.remove(nearest)

        for x, y in ordered:
            pattern.add_stitch_absolute(pe.STITCH, x * scale, y * scale)

    return pattern


def processar_imagem(arquivo_path: str, tecido: str = "generico") -> pe.EmbPattern:
    """Detecta formato e processa SVG ou PNG para EmbPattern."""
    lower = arquivo_path.lower()
    if lower.endswith(".svg"):
        return svg_para_pattern(arquivo_path)
    elif lower.endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
        return png_para_pattern(arquivo_path)
    else:
        raise ValueError(f"Formato nao suportado: {lower}")
