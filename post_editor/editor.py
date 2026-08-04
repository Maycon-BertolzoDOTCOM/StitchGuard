"""Post-editor — operações de pós-edição em matrizes de bordado.

Operações disponíveis:
1. compensacao_pull — desloca pontos perpendicularmente à costura
2. ajustar_densidade — reamostra pontos (mais/menos ralo)
3. reordenar_blocos — reordena sequência de costura
4. inserir_ponto — adiciona ponto em posição específica
5. remover_ponto — remove ponto por índice
6. adicionar_underlay — adiciona pontos de suporte
7. remover_underlay — remove pontos de suporte
"""
import math
import os
import uuid

import pyembroidery as pe


# ---------------------------------------------------------------------------
# Operações de pós-edição
# ---------------------------------------------------------------------------

def compensacao_pull(pattern: pe.EmbPattern, valor_mm: float = 0.5) -> pe.EmbPattern:
    """Desloca pontos perpendicularmente à direção da costura.

    Usado para compensar o efeito de "pull" (puxão) do tecido.
    Pontos são deslocados na direção perpendicular ao vetor de costura,
    com magnitude proporcional ao comprimento do ponto.

    Args:
        pattern: padrão de bordado
        valor_mm: deslocamento máximo em mm (positivo = para fora, negativo = para dentro)

    Returns:
        Novo padrão com compensação aplicada
    """
    new_pattern = pe.EmbPattern()
    new_pattern.threadlist = list(pattern.threadlist)

    stitches = list(pattern.stitches)
    if not stitches:
        return new_pattern

    result = []
    prev_x, prev_y = None, None

    for x, y, cmd in stitches:
        if cmd == pe.STITCH and prev_x is not None:
            dx = x - prev_x
            dy = y - prev_y
            length = math.hypot(dx, dy)

            if length > 0.01:
                # Vetor perpendicular (normalizado)
                nx, ny = -dy / length, dx / length
                # Escalar pelo valor de compensação
                offset_x = nx * valor_mm
                offset_y = ny * valor_mm
                result.append((x + offset_x, y + offset_y, cmd))
            else:
                result.append((x, y, cmd))
        else:
            result.append((x, y, cmd))

        if cmd in (pe.STITCH, pe.JUMP, pe.STOP):
            prev_x, prev_y = x, y

    for x, y, cmd in result:
        new_pattern.add_stitch_absolute(cmd, x, y)

    return new_pattern


def ajustar_densidade(pattern: pe.EmbPattern, fator: float = 1.0) -> pe.EmbPattern:
    """Reamostra pontos para ajustar densidade.

    fator < 1.0 = mais denso (pontos mais próximos)
    fator > 1.0 = menos denso (pontos mais espaçados)
    fator == 1.0 = sem alteração

    Args:
        pattern: padrão de bordado
        fator: fator de escala (0.5 = 2x mais denso, 2.0 = 2x menos denso)

    Returns:
        Novo padrão com densidade ajustada
    """
    new_pattern = pe.EmbPattern()
    new_pattern.threadlist = list(pattern.threadlist)

    stitches = list(pattern.stitches)
    if not stitches or fator == 1.0:
        return pattern

    result = []
    prev_x, prev_y = None, None

    for x, y, cmd in stitches:
        if cmd == pe.STITCH and prev_x is not None:
            dx = x - prev_x
            dy = y - prev_y
            # Escalar distância pelo fator
            new_x = prev_x + dx * fator
            new_y = prev_y + dy * fator
            result.append((new_x, new_y, cmd))
        else:
            result.append((x, y, cmd))

        if cmd in (pe.STITCH, pe.JUMP, pe.STOP):
            prev_x, prev_y = result[-1][0], result[-1][1]

    for x, y, cmd in result:
        new_pattern.add_stitch_absolute(cmd, x, y)

    return new_pattern


def reordenar_blocos(pattern: pe.EmbPattern, nova_ordem: list[int]) -> pe.EmbPattern:
    """Reordena blocos de cor (sequência de costura).

    Args:
        pattern: padrão de bordado
        nova_ordem: lista de índices dos blocos na nova ordem
                    (ex: [2, 0, 1] = bloco 2 primeiro, depois 0, depois 1)

    Returns:
        Novo padrão com blocos reordenados
    """
    new_pattern = pe.EmbPattern()
    new_pattern.threadlist = list(pattern.threadlist)

    blocos = list(pattern.get_as_colorblocks())
    if not blocos:
        return new_pattern

    # Validar ordem
    max_idx = len(blocos) - 1
    for idx in nova_ordem:
        if idx < 0 or idx > max_idx:
            raise ValueError(f"Índice {idx} fora do range [0, {max_idx}]")

    # Adicionar blocos na nova ordem
    first = True
    result = []
    for idx in nova_ordem:
        stitches, thread = blocos[idx]
        if not first:
            # JUMP entre blocos
            last = result[-1] if result else (0, 0, pe.STITCH)
            new_pattern.add_stitch_absolute(pe.JUMP, last[0], last[1])
        first = False

        for x, y, cmd in stitches:
            new_pattern.add_stitch_absolute(cmd, x, y)
            result.append((x, y, cmd))

    return new_pattern


def inserir_ponto(pattern: pe.EmbPattern, indice: int, x: float, y: float) -> pe.EmbPattern:
    """Insere um ponto em posição específica.

    Args:
        pattern: padrão de bordado
        indice: posição para inserir (0 = início, -1 = fim)
        x, y: coordenadas do novo ponto

    Returns:
        Novo padrão com ponto inserido
    """
    new_pattern = pe.EmbPattern()
    new_pattern.threadlist = list(pattern.threadlist)

    stitches = list(pattern.stitches)
    if indice < 0:
        indice = len(stitches) + indice + 1
    indice = max(0, min(indice, len(stitches)))

    for i, (sx, sy, cmd) in enumerate(stitches):
        if i == indice:
            new_pattern.add_stitch_absolute(pe.STITCH, x, y)
        new_pattern.add_stitch_absolute(cmd, sx, sy)

    if indice >= len(stitches):
        new_pattern.add_stitch_absolute(pe.STITCH, x, y)

    return new_pattern


def remover_ponto(pattern: pe.EmbPattern, indice: int) -> pe.EmbPattern:
    """Remove ponto por índice.

    Args:
        pattern: padrão de bordado
        índice: posição do ponto a remover

    Returns:
        Novo padrão com ponto removido
    """
    new_pattern = pe.EmbPattern()
    new_pattern.threadlist = list(pattern.threadlist)

    stitches = list(pattern.stitches)
    if indice < 0:
        indice = len(stitches) + indice
    if indice < 0 or indice >= len(stitches):
        raise ValueError(f"Índice {indice} fora do range [0, {len(stitches) - 1}]")

    for i, (x, y, cmd) in enumerate(stitches):
        if i != indice:
            new_pattern.add_stitch_absolute(cmd, x, y)

    return new_pattern


def adicionar_underlay(pattern: pe.EmbPattern, tipo: str = "walking") -> pe.EmbPattern:
    """Adiciona pontos de suporte (underlay) antes dos pontos principais.

    Tipos de underlay:
    - "walking": pontos de caminhada (mais denso)
    - "zigzag": pontos em ziguezague

    Args:
        pattern: padrão de bordado
        tipo: tipo de underlay ("walking" ou "zigzag")

    Returns:
        Novo padrão com underlay adicionado
    """
    new_pattern = pe.EmbPattern()
    new_pattern.threadlist = list(pattern.threadlist)

    blocos = list(pattern.get_as_colorblocks())
    if not blocos:
        return new_pattern

    first = True
    for stitches, thread in blocos:
        if not first:
            last = result[-1] if result else (0, 0, pe.STITCH)
            new_pattern.add_stitch_absolute(pe.JUMP, last[0], last[1])
        first = False

        # Extrair pontos STITCH do bloco
        stitch_points = [(x, y) for x, y, cmd in stitches if cmd == pe.STITCH]

        if stitch_points and len(stitch_points) > 1:
            # Gerar underlay
            if tipo == "zigzag":
                underlay_pts = _gerar_underlay_zigzag(stitch_points)
            else:
                underlay_pts = _gerar_underlay_walking(stitch_points)

            # Adicionar underlay
            for x, y in underlay_pts:
                new_pattern.add_stitch_absolute(pe.STITCH, x, y)

        # Adicionar pontos originais
        for x, y, cmd in stitches:
            new_pattern.add_stitch_absolute(cmd, x, y)

    return new_pattern


def _gerar_underlay_walking(pontos: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Gera underlay de caminhada: desloca pontos levemente para dentro."""
    if len(pontos) < 2:
        return []

    result = []
    offset = 0.3  # mm para dentro

    for i, (x, y) in enumerate(pontos):
        if i < len(pontos) - 1:
            nx, ny = pontos[i + 1]
        else:
            nx, ny = pontos[i - 1] if i > 0 else (x, y)

        dx = nx - x
        dy = ny - y
        length = math.hypot(dx, dy)

        if length > 0.01:
            # Vetor perpendicular
            px, py = -dy / length, dx / length
            result.append((x + px * offset, y + py * offset))
        else:
            result.append((x, y))

    return result


def _gerar_underlay_zigzag(pontos: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Gera underlay em ziguezague: alterna pontos à esquerda e direita."""
    if len(pontos) < 2:
        return []

    result = []
    offset = 0.4  # mm

    for i, (x, y) in enumerate(pontos):
        if i < len(pontos) - 1:
            nx, ny = pontos[i + 1]
        else:
            nx, ny = pontos[i - 1] if i > 0 else (x, y)

        dx = nx - x
        dy = ny - y
        length = math.hypot(dx, dy)

        if length > 0.01:
            px, py = -dy / length, dx / length
            # Alternar lado
            side = 1 if i % 2 == 0 else -1
            result.append((x + px * offset * side, y + py * offset * side))
        else:
            result.append((x, y))

    return result


def remover_underlay(pattern: pe.EmbPattern, tolerancia_mm: float = 0.5) -> pe.EmbPattern:
    """Remove pontos de suporte (underlay) baseado em heurística.

    Detecta underlay como pontos com comprimento muito curto (< tolerancia)
    que precedem pontos mais longos no mesmo bloco.

    Args:
        pattern: padrão de bordado
        tolerancia_mm: comprimento máximo para considerar como underlay

    Returns:
        Novo padrão sem underlay
    """
    new_pattern = pe.EmbPattern()
    new_pattern.threadlist = list(pattern.threadlist)

    stitches = list(pattern.stitches)
    if not stitches:
        return new_pattern

    # Detectar underlay: pontos muito curtos seguidos por pontos mais longos
    result = []
    i = 0
    while i < len(stitches):
        x, y, cmd = stitches[i]

        if cmd == pe.STITCH and i + 1 < len(stitches):
            # Verificar se próximo ponto é mais longo
            nx, ny, ncmd = stitches[i + 1]
            if ncmd == pe.STITCH:
                dist = math.hypot(nx - x, ny - y)
                # Se distância curta, pode ser underlay
                if dist < tolerancia_mm:
                    # Pular este ponto (é underlay)
                    i += 1
                    continue

        result.append((x, y, cmd))
        i += 1

    for x, y, cmd in result:
        new_pattern.add_stitch_absolute(cmd, x, y)

    return new_pattern


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def carregar_pattern(caminho: str) -> pe.EmbPattern:
    """Carrega padrão de bordado de arquivo."""
    return pe.read(caminho)


def salvar_pattern(pattern: pe.EmbPattern, caminho: str) -> str:
    """Salva padrão de bordado em arquivo."""
    pe.write(pattern, caminho)
    return caminho


def pattern_para_svg(pattern: pe.EmbPattern) -> str:
    """Converte padrão para SVG usando pyembroidery nativo."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        pe.write(pattern, tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def aplicar_operacoes(caminho_dst: str, operacoes: list[dict]) -> dict:
    """Aplica lista de operações de pós-edição.

    Args:
        caminho_dst: caminho do arquivo .dst original
        operacoes: lista de dicts com 'tipo' e parâmetros

    Returns:
        dict com pattern editado, SVG e estatísticas
    """
    pattern = carregar_pattern(caminho_dst)
    stats_original = {
        "pontos": len(list(pattern.stitches)),
        "largura_mm": round(pattern.bounds()[2] - pattern.bounds()[0], 2),
        "altura_mm": round(pattern.bounds()[3] - pattern.bounds()[1], 2),
    }

    for op in operacoes:
        tipo = op.get("tipo")
        if tipo == "compensacao_pull":
            pattern = compensacao_pull(pattern, valor_mm=op.get("valor_mm", 0.5))
        elif tipo == "ajustar_densidade":
            pattern = ajustar_densidade(pattern, fator=op.get("fator", 1.0))
        elif tipo == "reordenar_blocos":
            pattern = reordenar_blocos(pattern, nova_ordem=op.get("ordem", []))
        elif tipo == "inserir_ponto":
            pattern = inserir_ponto(pattern, indice=op.get("indice", 0),
                                    x=op.get("x", 0), y=op.get("y", 0))
        elif tipo == "remover_ponto":
            pattern = remover_ponto(pattern, indice=op.get("indice", 0))
        elif tipo == "adicionar_underlay":
            pattern = adicionar_underlay(pattern, tipo=op.get("tipo_underlay", "walking"))
        elif tipo == "remover_underlay":
            pattern = remover_underlay(pattern, tolerancia_mm=op.get("tolerancia_mm", 0.5))
        else:
            raise ValueError(f"Operação desconhecida: {tipo}")

    stats_editado = {
        "pontos": len(list(pattern.stitches)),
        "largura_mm": round(pattern.bounds()[2] - pattern.bounds()[0], 2),
        "altura_mm": round(pattern.bounds()[3] - pattern.bounds()[1], 2),
    }

    svg = pattern_para_svg(pattern)

    return {
        "pattern": pattern,
        "svg": svg,
        "stats_original": stats_original,
        "stats_editado": stats_editado,
        "operacoes_aplicadas": [op.get("tipo") for op in operacoes],
    }
