#!/usr/bin/env python3
"""Download de datasets para StitchGuard.

Datasets suportados:
- MSEmbGAN: 30k imagens de bordado (Universidade Têxtil de Wuhan)
- Embroidery Streamlines: Pesquisa HKU

Uso:
    python datasets/download_msembgan.py --output ./datasets
    python datasets/download_msembgan.py --dataset msembgan --output ./datasets
    python datasets/download_msembgan.py --skip-download  # apenas estrutura
"""
import argparse
import hashlib
import os
import subprocess
import sys
import zipfile
from pathlib import Path

# URLs verificadas dos datasets
DATASET_URLS = {
    "msembgan": {
        "description": "MSEmbGAN Dataset - 30k imagens de bordado com anotações",
        "github": "https://github.com/MSEmbGAN/MSEmbGAN-Dataset",
        "size_gb": 2.5,
        "structure": [
            "images/embroidery/",
            "images/content/",
            "annotations/",
        ],
    },
    "embroidery_streamlines": {
        "description": "Embroidery Streamlines - Pesquisa HKU sobre streamlines",
        "github": "https://github.com/embroidery-streamlines/embroidery-streamlines",
        "size_gb": 0.5,
        "structure": [
            "samples/",
            "models/",
        ],
    },
}


def criar_estrutura_diretorios(output_dir: str):
    """Cria estrutura de diretórios para o dataset."""
    dirs = [
        "msembgan/images/embroidery",
        "msembgan/images/content",
        "msembgan/annotations",
        "embroidery_streamlines/samples",
        "embroidery_streamlines/models",
        "processed",
        "processed/classifier",
        "processed/recommender",
    ]
    for d in dirs:
        path = os.path.join(output_dir, d)
        os.makedirs(path, exist_ok=True)
        print(f"  ✓ {path}")


def gerar_readme(output_dir: str):
    """Gera README.md para o diretório de datasets."""
    readme = """# Datasets para StitchGuard

## MSEmbGAN Dataset

**Descrição:** 30.000+ imagens de bordado com anotações de tipos de ponto.

**Fonte:** Universidade Têxtil de Wuhan (Professor Hu Ximrong)

**Conteúdo:**
- `images/embroidery/` - Imagens finais de bordado
- `images/content/` - Imagens de conteúdo original (arte de entrada)
- `annotations/` - Anotações de ponto único e múltiplos pontos

**Uso no StitchGuard:**
1. Treinar classificador de tipos de ponto (satin, fill, running)
2. Criar sistema de recomendação de parâmetros
3. Validar modelos contra benchmark acadêmico

**Como baixar:**
```bash
# Baixa tudo
python datasets/download_msembgan.py --output ./datasets

# Apenas estrutura (sem download)
python datasets/download_msembgan.py --skip-download
```

**Formato das anotações:**
```json
{
  "image_id": "00001",
  "stitch_types": ["satin", "fill", "running"],
  "regions": [
    {"type": "satin", "bbox": [x, y, w, h]},
    {"type": "fill", "bbox": [x, y, w, h]}
  ]
}
```

## Embroidery Streamlines

**Descrição:** Pesquisa da Universidade de Hong Kong sobre streamlines de bordado.

**Fonte:** embroidery-streamlines (GitHub)

**Conteúdo:**
- `samples/` - Exemplos de bordado
- `models/` - Modelos treinados

**Uso no StitchGuard:**
- Referência para algoritmos de geração de caminhos
- Base para futuras implementações de IA

## Processed

Dados processados para treinamento:
- `classifier/` - Dados para classificador de tipos de ponto
- `recommender/` - Dados para recomendador de parâmetros

## Dados Proprietários (futuro)

Com o StitchGuard em produção, coletaremos:
- Parâmetros reais usados por tecido
- Resultados de validação
- Feedback do clientes

Meta: 500-1.000 matrizes reais para dataset proprietário.
"""
    with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"  ✓ {output_dir}/README.md")


def verificar_dependencias() -> bool:
    """Verifica dependências necessárias."""
    deps_ok = True

    try:
        import requests
        print("  ✓ requests instalado")
    except ImportError:
        print("  ✗ requests não instalado")
        print("    → pip install requests")
        deps_ok = False

    return deps_ok


def download_github_repo(repo_url: str, output_dir: str, repo_name: str) -> bool:
    """Baixa repositório do GitHub via git clone."""
    dest = os.path.join(output_dir, repo_name)
    if os.path.exists(dest):
        print(f"  ⏭ {repo_name} já existe, pulando...")
        return True

    print(f"  ↓ Baixando {repo_name}...")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, dest],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos timeout
        )
        print(f"  ✓ {repo_name} baixado com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Erro ao baixar {repo_name}")
        if e.stderr:
            print(f"    {e.stderr[:200]}")
        return False
    except FileNotFoundError:
        print("  ✗ Git não encontrado. Instale git.")
        return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout ao baixar {repo_name}")
        return False


def verificar_dataset(output_dir: str, dataset_name: str) -> dict:
    """Verifica integridade do dataset baixado."""
    info = DATASET_URLS.get(dataset_name)
    if not info:
        return {"ok": False, "error": "Dataset desconhecido"}

    dataset_dir = os.path.join(output_dir, dataset_name)
    if not os.path.exists(dataset_dir):
        return {"ok": False, "error": "Diretório não encontrado"}

    # Contar arquivos
    total_files = 0
    total_size = 0
    for root, dirs, files in os.walk(dataset_dir):
        for f in files:
            total_files += 1
            total_size += os.path.getsize(os.path.join(root, f))

    return {
        "ok": total_files > 0,
        "files": total_files,
        "size_mb": round(total_size / (1024 * 1024), 2),
        "path": dataset_dir,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Download de datasets para StitchGuard"
    )
    parser.add_argument(
        "--output",
        default="./datasets",
        help="Diretório de saída (padrão: ./datasets)"
    )
    parser.add_argument(
        "--dataset",
        choices=["all", "msembgan", "streamlines"],
        default="all",
        help="Dataset para baixar (padrão: all)"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Apenas criar estrutura e README, sem baixar"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Apenas verificar datasets existentes"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("StitchGuard - Download de Datasets")
    print("=" * 50)

    # Criar diretório de saída
    os.makedirs(args.output, exist_ok=True)

    # Verificar datasets existentes
    if args.verify:
        print("\nVerificando datasets...")
        for name in DATASET_URLS:
            info = verificar_dataset(args.output, name)
            if info["ok"]:
                print(f"  ✓ {name}: {info['files']} arquivos ({info['size_mb']} MB)")
            else:
                print(f"  ✗ {name}: {info.get('error', 'não encontrado')}")
        return

    # Criar estrutura
    print("\n1. Criando estrutura de diretórios...")
    criar_estrutura_diretorios(args.output)

    # Gerar README
    print("\n2. Gerando documentação...")
    gerar_readme(args.output)

    if args.skip_download:
        print("\n✓ Estrutura criada (sem download).")
        print(f"  Diretório: {args.output}")
        print("\nPara baixar depois:")
        print("  python datasets/download_msembgan.py --output ./datasets")
        return

    # Verificar dependências
    print("\n3. Verificando dependências...")
    if not verificar_dependencias():
        print("\n⚠ Instale as dependências:")
        print("  pip install requests")
        sys.exit(1)

    # Baixar datasets
    print("\n4. Baixando datasets...")
    resultados = {}

    if args.dataset in ("all", "msembgan"):
        info = DATASET_URLS["msembgan"]
        print(f"\n  [{info['description']}]")
        ok = download_github_repo(info["github"], args.output, "msembgan")
        resultados["msembgan"] = ok

    if args.dataset in ("all", "streamlines"):
        info = DATASET_URLS["embroidery_streamlines"]
        print(f"\n  [{info['description']}]")
        ok = download_github_repo(info["github"], args.output, "embroidery_streamlines")
        resultados["streamlines"] = ok

    # Resumo
    print("\n" + "=" * 50)
    print("Resumo:")
    for name, ok in resultados.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")

    # Verificar
    print("\nVerificação:")
    for name in resultados:
        if resultados[name]:
            info = verificar_dataset(args.output, name)
            if info["ok"]:
                print(f"  ✓ {name}: {info['files']} arquivos ({info['size_mb']} MB)")
            else:
                print(f"  ✗ {name}: vazio ou corrompido")

    print("\nPróximos passos:")
    print("  1. Verificar conteúdo baixado")
    print("  2. Processar imagens: python datasets/processar.py")
    print("  3. Treinar classificador")


if __name__ == "__main__":
    main()
