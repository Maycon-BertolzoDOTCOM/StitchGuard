#!/usr/bin/env python3
"""Processamento de datasets para treinamento.

Converte imagens baixadas em dados processados para:
- Classificador de tipos de ponto
- Recomendador de parâmetros

Uso:
    python datasets/processar.py --input ./datasets --output ./datasets/processed
"""
import argparse
import json
import os
from pathlib import Path


def processar_msembgan(input_dir: str, output_dir: str) -> dict:
    """Processa dataset MSEmbGAN para classificador.

    Lê anotações e cria CSV/JSON para treinamento.
    """
    annotations_dir = os.path.join(input_dir, "msembgan", "annotations")
    images_dir = os.path.join(input_dir, "msembgan", "images")

    if not os.path.exists(annotations_dir):
        print(f"  ✗ Diretório de anotações não encontrado: {annotations_dir}")
        return {"ok": False, "samples": 0}

    # Listar anotações
    annotations = []
    for root, dirs, files in os.walk(annotations_dir):
        for f in files:
            if f.endswith(".json"):
                annotations.append(os.path.join(root, f))

    if not annotations:
        print("  ⚠ Nenhuma anotação encontrada")
        return {"ok": False, "samples": 0}

    print(f"  Encontradas {len(annotations)} anotações")

    # Processar cada anotação
    classifier_data = []
    for ann_path in annotations:
        try:
            with open(ann_path, "r", encoding="utf-8") as f:
                ann = json.load(f)

            # Extrair informações relevantes
            sample = {
                "image_id": ann.get("image_id", os.path.basename(ann_path)),
                "stitch_types": ann.get("stitch_types", []),
                "regions": ann.get("regions", []),
            }
            classifier_data.append(sample)
        except Exception as e:
            print(f"  ⚠ Erro ao processar {ann_path}: {e}")

    # Salvar dados processados
    output_file = os.path.join(output_dir, "classifier", "dataset.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(classifier_data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Dados do classificador: {output_file}")
    print(f"    {len(classifier_data)} amostras processadas")

    return {"ok": True, "samples": len(classifier_data)}


def criar_treino_exemplo(output_dir: str):
    """Cria dados de treino de exemplo para demonstração."""
    train_data = [
        {
            "image_id": "exemplo_001",
            "stitch_types": ["satin"],
            "regions": [{"type": "satin", "bbox": [0, 0, 50, 10]}],
            "fabric": "jeans",
            "density": 0.45,
        },
        {
            "image_id": "exemplo_002",
            "stitch_types": ["fill"],
            "regions": [{"type": "fill", "bbox": [0, 0, 30, 30]}],
            "fabric": "malha",
            "density": 0.40,
        },
        {
            "image_id": "exemplo_003",
            "stitch_types": ["running"],
            "regions": [{"type": "running", "bbox": [0, 0, 100, 5]}],
            "fabric": "nylon",
            "density": 0.50,
        },
    ]

    output_file = os.path.join(output_dir, "classifier", "exemplos.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Exemplos de treino: {output_file}")
    return len(train_data)


def main():
    parser = argparse.ArgumentParser(
        description="Processamento de datasets para StitchGuard"
    )
    parser.add_argument(
        "--input",
        default="./datasets",
        help="Diretório de entrada (datasets baixados)"
    )
    parser.add_argument(
        "--output",
        default="./datasets/processed",
        help="Diretório de saída (dados processados)"
    )
    parser.add_argument(
        "--only-examples",
        action="store_true",
        help="Apenas criar dados de exemplo"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("StitchGuard - Processamento de Datasets")
    print("=" * 50)

    os.makedirs(args.output, exist_ok=True)

    if args.only_examples:
        print("\nCriando dados de exemplo...")
        n = criar_treino_exemplo(args.output)
        print(f"\n✓ {n} exemplos criados")
        return

    # Processar MSEmbGAN
    print("\n1. Processando MSEmbGAN...")
    result = processar_msembgan(args.input, args.output)

    # Criar exemplos se não houver dados reais
    if not result["ok"] or result["samples"] == 0:
        print("\n2. Criando dados de exemplo...")
        criar_treino_exemplo(args.output)

    print("\n" + "=" * 50)
    print("✓ Processamento concluído!")
    print(f"  Saída: {args.output}")
    print("\nPróximos passos:")
    print("  1. Treinar classificador: python ml/train_classifier.py")
    print("  2. Avaliar modelo: python ml/evaluate.py")


if __name__ == "__main__":
    main()
