"""Batch processing — processa múltiplas imagens de uma vez.

Para ateliês que recebem vários pedidos por dia.
Endpoint: POST /v1/batch
"""
import os
import uuid
import tempfile
from typing import Optional

import structlog

log = structlog.get_logger()


def processar_batch(
    arquivos: list[dict],
    tecido: str = "generico",
    formato_saida: str = "dst",
) -> dict:
    """Processa múltiplas imagens em batch.

    Args:
        arquivos: Lista de dicts {filename, path}
        tecido: Tipo de tecido para todos
        formato_saida: Formato de saída (dst/pes/exp)

    Returns:
        Dict com resultados e estatísticas
    """
    import pyembroidery as pe
    from generation.inkstitch_provider import auto_digitize
    from generation.providers.cli_anything import generate as cli_generate

    resultados = []
    erros = []
    total_pontos = 0
    total_cores = 0

    for i, arq in enumerate(arquivos):
        filename = arq.get("filename", f"arquivo_{i}")
        path = arq.get("path")

        if not path or not os.path.exists(path):
            erros.append({"filename": filename, "erro": "Arquivo não encontrado"})
            continue

        try:
            ext = os.path.splitext(filename)[1].lower()

            if ext in (".dst", ".pes", ".exp", ".vp3"):
                # Já é arquivo de bordado - apenas copiar
                dst_nome = f"{uuid.uuid4().hex[:8]}{ext}"
                dst_path = os.path.join(_ARTEFATOS, dst_nome)
                import shutil
                shutil.copy2(path, dst_path)

                resultados.append({
                    "filename": filename,
                    "dst": dst_nome,
                    "status": "copiado",
                    "pontos": 0,
                })
            elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
                # Imagem - auto-digitize
                pontos = auto_digitize(path, tecido=tecido)

                if not pontos:
                    erros.append({"filename": filename, "erro": "Nenhum ponto gerado"})
                    continue

                # Converter para pattern
                pattern = pe.EmbPattern()
                for p in pontos:
                    tipo = p.get("type", "STITCH")
                    if tipo == "JUMP":
                        pattern.add_stitch_absolute(pe.JUMP, p["x"], p["y"])
                    elif tipo == "TRIM":
                        pattern.add_stitch_absolute(pe.TRIM, p["x"], p["y"])
                    else:
                        pattern.add_stitch_absolute(pe.STITCH, p["x"], p["y"])
                pattern.add_command(pe.END)

                # Salvar
                dst_nome = f"{uuid.uuid4().hex[:8]}.{formato_saida}"
                dst_path = os.path.join(_ARTEFATOS, dst_nome)
                pe.write(pattern, dst_path)

                n_stitches = len(pattern.stitches)
                n_cores = len(list(pattern.get_as_colorblocks()))
                total_pontos += n_stitches
                total_cores += n_cores

                resultados.append({
                    "filename": filename,
                    "dst": dst_nome,
                    "status": "convertido",
                    "pontos": n_stitches,
                    "cores": n_cores,
                })
            else:
                erros.append({"filename": filename, "erro": f"Formato {ext} não suportado"})

        except Exception as e:
            erros.append({"filename": filename, "erro": str(e)})

    return {
        "total": len(arquivos),
        "processados": len(resultados),
        "erros": len(erros),
        "resultados": resultados,
        "detalhes_erros": erros,
        "estatisticas": {
            "total_pontos": total_pontos,
            "total_cores": total_cores,
            "pontos_medios": total_pontos // max(len(resultados), 1),
        },
    }


# Directório de artefatos (importado do main.py)
_ARTEFATOS = tempfile.mkdtemp(prefix="stitchguard-batch-")
