#!/usr/bin/env python3
"""Monitor de pastas INPUT/OUTPUT — processamento local de matrizes.

Uso:
    # Processar uma vez
    python scripts/monitor.py --once

    # Monitorar continuamente
    python scripts/monitor.py --watch

    # Processar arquivo específico
    python scripts/monitor.py --file input/minha_arte.png

Fluxo:
1. Monitora pasta INPUT/ por novos arquivos (SVG/PNG)
2. Converte automaticamente para .DST
3. Move resultado para pasta OUTPUT/
4. Gera relatório de processamento
"""
import argparse
import os
import shutil
import sys
import time
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyembroidery as pe


def processar_arquivo(input_path: str, output_dir: str) -> dict:
    """Processa um arquivo (SVG/PNG) e gera .DST."""
    from generation.image_processor import processar_imagem

    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        return {"ok": False, "error": f"Arquivo não encontrado: {input_path}"}

    # Detectar formato
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in (".svg", ".png", ".jpg", ".jpeg", ".bmp", ".gif"):
        return {"ok": False, "error": f"Formato não suportado: {ext}"}

    try:
        # Processar imagem
        pattern = processar_imagem(input_path)

        if not pattern.stitches:
            return {"ok": False, "error": "Nenhum ponto gerado"}

        # Gerar nome do arquivo de saída
        nome_base = os.path.splitext(os.path.basename(input_path))[0]
        dst_path = os.path.join(output_dir, f"{nome_base}.dst")

        # Salvar .DST
        pe.write(pattern, dst_path)

        # Gerar preview SVG
        svg_path = os.path.join(output_dir, f"{nome_base}_preview.svg")
        pe.write(pattern, svg_path)

        # Estatísticas
        bounds = pattern.bounds()
        stats = {
            "pontos": len(pattern.stitches),
            "cores": len(pattern.threadlist),
            "largura_mm": round(bounds[2] - bounds[0], 2),
            "altura_mm": round(bounds[3] - bounds[1], 2),
        }

        return {
            "ok": True,
            "input": input_path,
            "dst": dst_path,
            "preview": svg_path,
            "stats": stats,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def processar_pasta(input_dir: str, output_dir: str) -> list[dict]:
    """Processa todos os arquivos novos na pasta INPUT."""
    input_dir = os.path.abspath(input_dir)
    output_dir = os.path.abspath(output_dir)

    if not os.path.exists(input_dir):
        os.makedirs(input_dir, exist_ok=True)
        print(f"  Pasta INPUT criada: {input_dir}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"  Pasta OUTPUT criada: {output_dir}")

    resultados = []
    extensoes = (".svg", ".png", ".jpg", ".jpeg", ".bmp", ".gif")

    for arquivo in os.listdir(input_dir):
        if arquivo.lower().endswith(extensoes):
            input_path = os.path.join(input_dir, arquivo)
            print(f"\n  Processando: {arquivo}")

            resultado = processar_arquivo(input_path, output_dir)

            if resultado["ok"]:
                print(f"    ✓ {resultado['stats']['pontos']} pontos gerados")
                print(f"    ✓ {resultado['dst']}")

                # Mover arquivo processado para pasta processados/
                processados_dir = os.path.join(input_dir, "_processados")
                os.makedirs(processados_dir, exist_ok=True)
                shutil.move(input_path, os.path.join(processados_dir, arquivo))
            else:
                print(f"    ✗ Erro: {resultado['error']}")

            resultados.append(resultado)

    return resultados


def watch_mode(input_dir: str, output_dir: str, interval: int = 5):
    """Modo watch: monitora continuamente a pasta INPUT."""
    print(f"Modo watch: monitorando {input_dir} a cada {interval}s")
    print("Pressione Ctrl+C para parar\n")

    try:
        while True:
            processar_pasta(input_dir, output_dir)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatch interrompido")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor de pastas INPUT/OUTPUT para StitchGuard"
    )
    parser.add_argument(
        "--input",
        default="./INPUT",
        help="Pasta de entrada (padrão: ./INPUT)"
    )
    parser.add_argument(
        "--output",
        default="./OUTPUT",
        help="Pasta de saída (padrão: ./OUTPUT)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Processar uma vez e sair"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Monitorar continuamente"
    )
    parser.add_argument(
        "--file",
        help="Processar arquivo específico"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("StitchGuard - Monitor de Pastas")
    print("=" * 50)

    if args.file:
        # Processar arquivo específico
        print(f"\nProcessando arquivo: {args.file}")
        resultado = processar_arquivo(args.file, args.output)
        if resultado["ok"]:
            print(f"✓ Arquivo gerado: {resultado['dst']}")
            print(f"  Pontos: {resultado['stats']['pontos']}")
        else:
            print(f"✗ Erro: {resultado['error']}")
            sys.exit(1)

    elif args.watch:
        # Modo watch
        watch_mode(args.input, args.output)

    else:
        # Processar uma vez
        print(f"\nInput: {args.input}")
        print(f"Output: {args.output}")

        resultados = processar_pasta(args.input, args.output)

        # Resumo
        print("\n" + "=" * 50)
        print("Resumo:")
        sucessos = sum(1 for r in resultados if r["ok"])
        falhas = sum(1 for r in resultados if not r["ok"])
        print(f"  ✓ Sucessos: {sucessos}")
        print(f"  ✗ Falhas: {falhas}")

        if sucessos > 0:
            print("\nArquivos gerados:")
            for r in resultados:
                if r["ok"]:
                    print(f"  → {r['dst']}")


if __name__ == "__main__":
    main()
