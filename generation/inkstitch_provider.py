"""Provider Ink/Stitch — auto-digitizing gratuito e open-source.

Ink/Stitch é uma extensão do Inkscape que converte imagens em bordado.
Este módulo integra sua lógica de conversão sem precisar do Inkscape.

Referência: https://inkstitch.org/
Licença: GPL-3.0 (compatível com uso comercial)
"""
import os
import tempfile
from typing import Optional

import structlog

log = structlog.get_logger()

# Tentar importar dependências opcionais
try:
    import cv2
    import numpy as np
    from PIL import Image

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    log.warning("inkstitch.cv2_unavailable")

try:
    import potrace

    HAS_POTRACE = True
except ImportError:
    HAS_POTRACE = False


# ---------------------------------------------------------------------------
# Configuração de stitch por tecido (baseada em Ink/Stitch defaults)
# ---------------------------------------------------------------------------
STITCH_CONFIGS = {
    "malha": {
        "densidade": 4.0,  # pontos por mm
        "comprimento_max_mm": 4.0,
        "comprimento_min_mm": 0.5,
        "underlay": True,
        "underlay_tipo": "center_walk",
        "pull_compensation": 0.3,  # mm
        "push_compensation": 0.2,
    },
    "jeans": {
        "densidade": 4.5,
        "comprimento_max_mm": 3.5,
        "comprimento_min_mm": 0.5,
        "underlay": True,
        "underlay_tipo": "edge_walk",
        "pull_compensation": 0.4,
        "push_compensation": 0.3,
    },
    "nylon": {
        "densidade": 3.5,
        "comprimento_max_mm": 4.0,
        "comprimento_min_mm": 0.5,
        "underlay": True,
        "underlay_tipo": "zigzag",
        "pull_compensation": 0.2,
        "push_compensation": 0.1,
    },
    "bone": {
        "densidade": 5.0,
        "comprimento_max_mm": 3.0,
        "comprimento_min_mm": 0.5,
        "underlay": True,
        "underlay_tipo": "double_center_walk",
        "pull_compensation": 0.5,
        "push_compensation": 0.4,
    },
    "cetim": {
        "densidade": 3.5,
        "comprimento_max_mm": 4.5,
        "comprimento_min_mm": 0.5,
        "underlay": True,
        "underlay_tipo": "center_walk",
        "pull_compensation": 0.15,
        "push_compensation": 0.1,
    },
    "generico": {
        "densidade": 4.0,
        "comprimento_max_mm": 4.0,
        "comprimento_min_mm": 0.5,
        "underlay": True,
        "underlay_tipo": "center_walk",
        "pull_compensation": 0.3,
        "push_compensation": 0.2,
    },
}


def get_stitch_config(tecido: str) -> dict:
    """Retorna configuração de stitch para o tecido."""
    return STITCH_CONFIGS.get(tecido, STITCH_CONFIGS["generico"])


# ---------------------------------------------------------------------------
# Auto-digitizing: imagem → padrão de pontos
# ---------------------------------------------------------------------------
def auto_digitize(
    image_path: str,
    tecido: str = "generico",
    scale: float = 1.0,
    max_stitch_mm: float = 4.0,
    min_stitch_mm: float = 0.5,
    fill_angle: float = 45.0,
) -> list[dict]:
    """Converte imagem em lista de pontos de bordado.

    Algoritmo baseado no Ink/Stitch:
    1. Pré-processamento (grayscale, threshold, morphologia)
    2. Extração de contornos (OpenCV)
    3. Geração de pontos de preenchimento (raster fill)
    4. Geração de pontos de contorno (running stitch)

    Args:
        image_path: Caminho da imagem (PNG/JPG)
        tecido: Tipo de tecido (afeta densidade e compensação)
        scale: Fator de escala (1.0 = tamanho original em pixels → mm)
        max_stitch_mm: Comprimento máximo do ponto
        min_stitch_mm: Comprimento mínimo do ponto
        fill_angle: Ângulo de preenchimento em graus

    Returns:
        Lista de dicts com {x, y, type, color}
    """
    if not HAS_CV2:
        raise RuntimeError("OpenCV (cv2) é necessário para auto-digitizing. pip install opencv-python")

    config = get_stitch_config(tecido)
    densidade = config["densidade"]

    # 1. Carregar e pré-processar imagem
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Não foi possível carregar a imagem: {image_path}")

    # Threshold binário (Otsu)
    _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Operações morfológicas para limpar
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # 2. Encontrar contornos
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        raise ValueError("Nenhum contorno encontrado na imagem.")

    # 3. Escalar coordenadas (pixels → mm)
    pontos = []
    h, w = binary.shape

    # Ordenar contornos por área (maior primeiro)
    contours_sorted = sorted(contours, key=cv2.contourArea, reverse=True)

    for idx, contour in enumerate(contours_sorted):
        # Primeiro ponto do contorno
        first_pt = contour[0][0]
        fx, fy = int(first_pt[0]) * scale, int(first_pt[1]) * scale

        # TRIM entre contornos (na posição do próximo contorno)
        if idx > 0:
            pontos.append({"x": fx, "y": fy, "type": "JUMP", "color": 0})
            pontos.append({"x": fx, "y": fy, "type": "TRIM", "color": 0})

        # Lock stitch no início (STOP + tiny stitches)
        pontos.append({"x": fx, "y": fy, "type": "STOP", "color": 0})
        for offset in [0, 0.3, 0]:
            pontos.append({"x": fx + offset, "y": fy, "type": "STITCH", "color": 0})

        # Contorno (running stitch)
        contour_points = _simplificar_contorno(contour, max_stitch_mm)
        for x, y in contour_points:
            pontos.append({
                "x": x * scale,
                "y": y * scale,
                "type": "STITCH",
                "color": 0,
            })

        # Lock stitch no final (tiny stitches + STOP)
        last_pt = contour[-1][0]
        lx, ly = int(last_pt[0]) * scale, int(last_pt[1]) * scale
        for offset in [0, -0.3, 0]:
            pontos.append({"x": lx + offset, "y": ly, "type": "STITCH", "color": 0})
        pontos.append({"x": lx, "y": ly, "type": "STOP", "color": 0})

        # Preenchimento (fill stitch) para contornos grandes
        area = cv2.contourArea(contour)
        if area > 100:  # Só preencher se área significativa
            fill_points = _preenchimento_raster(contour, binary, densidade, fill_angle, scale)
            if fill_points:
                # JUMP + TRIM antes do preenchimento (na posição do primeiro ponto)
                first_fill = fill_points[0]
                pontos.append({"x": first_fill["x"], "y": first_fill["y"], "type": "JUMP", "color": 0})
                pontos.append({"x": first_fill["x"], "y": first_fill["y"], "type": "TRIM", "color": 0})
                pontos.extend(fill_points)

    # 4. Adicionar underlay se configurado
    if config["underlay"]:
        pontos = _adicionar_underlay(pontos, config, scale)

    # 5. Aplicar compensação pull/push
    pontos = _aplicar_compensacao(pontos, config)

    log.info("inkstitch.auto_digitize",
             pontos=len(pontos),
             contornos=len(contours),
             tecido=tecido)

    return pontos


def _simplificar_contorno(contour, max_stitch_mm: float) -> list[tuple]:
    """Simplifica contorno mantendo pontos a cada max_stitch_mm."""
    points = contour.reshape(-1, 2)
    if len(points) < 2:
        return [(int(p[0]), int(p[1])) for p in points]

    result = [(int(points[0][0]), int(points[0][1]))]
    dist_acum = 0.0

    for i in range(1, len(points)):
        dx = points[i][0] - points[i - 1][0]
        dy = points[i][1] - points[i - 1][1]
        dist = (dx**2 + dy**2) ** 0.5
        dist_acum += dist

        if dist_acum >= max_stitch_mm:
            result.append((int(points[i][0]), int(points[i][1])))
            dist_acum = 0.0

    return result


def _preenchimento_raster(
    contour,
    binary,
    densidade: float,
    angle: float,
    scale: float,
) -> list[dict]:
    """Gera pontos de preenchimento raster serpentine dentro do contorno.

    Usa padrão zigzag para minimizar jumps longos.
    """
    import math

    # Criar máscara do contorno
    mask = np.zeros_like(binary)
    cv2.fillPoly(mask, [contour], 255)

    # Bounds do contorno
    x, y, w, h = cv2.boundingRect(contour)
    pontos = []

    # Espaçamento entre linhas baseado na densidade (pontos/mm)
    spacing_px = max(2, int(1.0 / (densidade * scale)))

    # Centro do contorno
    cx, cy = x + w // 2, y + h // 2
    max_dim = max(w, h)

    # Gerar linhas de preenchimento (serpentine)
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    line_num = 0
    for offset in range(-max_dim, max_dim, spacing_px):
        # Linha perpendicular ao ângulo
        x1 = cx + offset
        y1 = cy - max_dim
        x2 = cx + offset
        y2 = cy + max_dim

        # Rotacionar
        rx1 = cos_a * (x1 - cx) - sin_a * (y1 - cy) + cx
        ry1 = sin_a * (x1 - cx) + cos_a * (y1 - cy) + cy
        rx2 = cos_a * (x2 - cx) - sin_a * (y2 - cy) + cx
        ry2 = sin_a * (x2 - cx) + cos_a * (y2 - cy) + cy

        # Coletar pontos dentro da máscara
        linha_pontos = []
        steps = max(1, int(((rx2 - rx1) ** 2 + (ry2 - ry1) ** 2) ** 0.5 / 0.5))
        for t in range(steps):
            px = rx1 + (rx2 - rx1) * t / steps
            py = ry1 + (ry2 - ry1) * t / steps
            if 0 <= int(py) < mask.shape[0] and 0 <= int(px) < mask.shape[1]:
                if mask[int(py), int(px)] > 0:
                    linha_pontos.append((px, py))

        # Adicionar pontos em ordem serpentine
        if linha_pontos:
            if line_num % 2 == 0:
                for px, py in linha_pontos:
                    pontos.append({"x": px * scale, "y": py * scale, "type": "STITCH", "color": 0})
            else:
                for px, py in reversed(linha_pontos):
                    pontos.append({"x": px * scale, "y": py * scale, "type": "STITCH", "color": 0})
            line_num += 1

    return pontos


def _adicionar_underlay(pontos: list[dict], config: dict, scale: float) -> list[dict]:
    """Adiciona pontos de underlay (base) antes do preenchimento principal."""
    if not pontos:
        return pontos

    underlay_tipo = config.get("underlay_tipo", "center_walk")
    underlay_points = []

    # Calcular bounds
    xs = [p["x"] for p in pontos]
    ys = [p["y"] for p in pontos]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    if underlay_tipo == "center_walk":
        # Linha central vertical
        cx = (x_min + x_max) / 2
        underlay_points.append({"x": cx, "y": y_min, "type": "JUMP", "color": 0})
        underlay_points.append({"x": cx, "y": y_max, "type": "STITCH", "color": 0})

    elif underlay_tipo == "edge_walk":
        # Contorno do underlay (offset para dentro)
        margin = 0.5 * scale
        underlay_points.append({"x": x_min + margin, "y": y_min + margin, "type": "JUMP", "color": 0})
        underlay_points.append({"x": x_max - margin, "y": y_min + margin, "type": "STITCH", "color": 0})
        underlay_points.append({"x": x_max - margin, "y": y_max - margin, "type": "STITCH", "color": 0})
        underlay_points.append({"x": x_min + margin, "y": y_max - margin, "type": "STITCH", "color": 0})
        underlay_points.append({"x": x_min + margin, "y": y_min + margin, "type": "STITCH", "color": 0})

    elif underlay_tipo == "zigzag":
        # Zigzag de underlay
        spacing = 1.0 / config["densidade"] * 2
        y = y_min + spacing
        while y < y_max:
            underlay_points.append({"x": x_min, "y": y, "type": "STITCH", "color": 0})
            underlay_points.append({"x": x_max, "y": y, "type": "STITCH", "color": 0})
            y += spacing

    elif underlay_tipo == "double_center_walk":
        # Duas linhas centrais
        cx = (x_min + x_max) / 2
        offset = 0.3 * scale
        underlay_points.append({"x": cx - offset, "y": y_min, "type": "JUMP", "color": 0})
        underlay_points.append({"x": cx - offset, "y": y_max, "type": "STITCH", "color": 0})
        underlay_points.append({"x": cx + offset, "y": y_max, "type": "STITCH", "color": 0})
        underlay_points.append({"x": cx + offset, "y": y_min, "type": "STITCH", "color": 0})

    # Underlay primeiro, depois pontos principais
    return underlay_points + pontos


def _aplicar_compensacao(pontos: list[dict], config: dict) -> list[dict]:
    """Aplica compensação pull/push aos pontos."""
    pull = config.get("pull_compensation", 0.0)
    push = config.get("push_compensation", 0.0)

    if pull == 0 and push == 0:
        return pontos

    # Compensação simplificada: ajustar pontos de contorno
    compensated = []
    for p in pontos:
        new_p = dict(p)
        # Aplicar compensação horizontal (pull) para pontos de contorno
        if p.get("type") == "STITCH":
            new_p["x"] = p["x"] + pull * 0.5  # Ajuste simplificado
        compensated.append(new_p)

    return compensated
