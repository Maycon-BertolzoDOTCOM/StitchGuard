"""StitchGuard - extração de métricas de arquivos de bordado (.DST)."""
import math
import pyembroidery as pe


class StitchMetrics:
    """Medições extraídas de um arquivo de bordado via pyembroidery."""

    def __init__(self, path):
        self.pattern = pe.read(path)
        self.stitches = list(self.pattern.stitches)
        self.threads = list(self.pattern.threadlist)
        bounds = self.pattern.bounds()
        self.extremes = bounds if isinstance(bounds, (tuple, list)) and len(bounds) == 4 else None
        self.color_breaks = self.pattern.count_color_changes()
        self.stitch_count = self.pattern.count_stitches()

    @property
    def width_mm(self):
        if not self.extremes:
            return 0.0
        return self.extremes[2] - self.extremes[0]

    @property
    def height_mm(self):
        if not self.extremes:
            return 0.0
        return self.extremes[3] - self.extremes[1]

    def jumps(self):
        """Lista de saltos (jumps) em mm com o comando que os causou.

        TRIM e COLOR_CHANGE NÃO são considerados jumps — representam
        corte de thread entre partes, não movimentação indevida.
        """
        jumps = []
        prev = None
        for item in self.stitches:
            x, y, cmd = item[0], item[1], item[2]
            if prev is not None:
                dx, dy = x - prev[0], y - prev[1]
                dist = math.hypot(dx, dy)
                if cmd == pe.JUMP:
                    jumps.append({"x": x, "y": y, "distance_mm": round(dist, 2), "command": cmd})
                elif cmd == pe.STITCH and dist > 12.0:
                    jumps.append({"x": x, "y": y, "distance_mm": round(dist, 2), "command": cmd})
            if cmd in (pe.STITCH, pe.JUMP, pe.STOP):
                prev = (x, y)
        return jumps

    def stitch_lengths(self):
        """Comprimento de cada ponto costurado (STITCH), em mm."""
        lengths = []
        prev = None
        for item in self.stitches:
            x, y, cmd = item[0], item[1], item[2]
            if prev is not None and cmd == pe.STITCH:
                dx, dy = x - prev[0], y - prev[1]
                lengths.append(math.hypot(dx, dy))
            if cmd in (pe.STITCH, pe.JUMP, pe.STOP):
                prev = (x, y)
        return lengths

    def average_stitch_length_mm(self):
        lengths = self.stitch_lengths()
        if not lengths:
            return 0.0
        return sum(lengths) / len(lengths)

    def max_jump_mm(self):
        jumps = self.jumps()
        return max((j["distance_mm"] for j in jumps), default=0.0)

    def stops(self):
        return sum(1 for item in self.stitches if item[2] in (pe.STOP, pe.COLOR_CHANGE))

    def trims(self):
        return sum(1 for item in self.stitches if item[2] == pe.TRIM)

    def thread_colors(self):
        return [
            {
                "color": t.get_color(),
                "hex": t.get_hex(),
                "name": t.get_description() or "",
            }
            for t in self.threads
        ]

    def blocos_centros(self):
        """Centros (x, y) de cada bloco de cor — usado pelo otimizador de sequencia.

        Retorna lista de tuplas (x_centro, y_centro). Um bloco sem pontos
        costurados (ex: só JUMP) recebe centro (0, 0) e e ignorado pelo
        otimizador quando o tamanho da lista for 1.
        """
        centros = []
        for stitches, _thread in self.pattern.get_as_colorblocks():
            xs, ys = [], []
            for x, y, cmd in stitches:
                if cmd == pe.STITCH:
                    xs.append(x)
                    ys.append(y)
            if xs and ys:
                centros.append((round(sum(xs) / len(xs), 2), round(sum(ys) / len(ys), 2)))
        return centros

    def density_stitches_per_cm(self):
        area_cm2 = (self.width_mm / 10.0) * (self.height_mm / 10.0)
        if area_cm2 <= 0:
            return 0.0
        return round(self.stitch_count / area_cm2, 2)
