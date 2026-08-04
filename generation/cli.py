"""StitchGuard - Pipeline completo: gerar -> validar -> otimizar.

Gera a matriz via ProviderRouter (L3), valida com o checklist (L4) e
imprime o relatório final, incluindo a otimização de saltos.
"""
import argparse
import json
import os
import sys

from generation.router import route
from validation.checklist import run_checklist
from validation.metrics import StitchMetrics

TECIDOS = ["malha", "jeans", "nylon", "bone", "cetim"]


def main():
    parser = argparse.ArgumentParser(
        prog="stitchguard-generate",
        description="Gera matriz de bordado a partir de um JSON de arte e valida (L3 -> L4).",
    )
    parser.add_argument("arte", nargs="?", help="Caminho do JSON de arte (omita p/ amostra padrão)")
    parser.add_argument("--tecido", choices=TECIDOS, default="generico")
    parser.add_argument("--preset", choices=["ralo", "padrao", "denso"], default=None,
                        help="Variante do dial p/ cetim (ralo|padrao|denso)")
    parser.add_argument("--compensacao", choices=["alta", "media", "baixa"], default=None)
    parser.add_argument("--underlay", action="store_true", help="Ativa underlay na geracao")
    parser.add_argument("--maquina", default=None, help="ID da maquina para validacao (ver domain/maquinas.py)")
    parser.add_argument("--dificuldade", choices=["low", "medium", "high"], default="low")
    parser.add_argument("--out", help="Caminho de saida do .dst (padrao: ao lado da arte)")
    parser.add_argument("--json", action="store_true", help="Saida em JSON (via stdout)")
    args = parser.parse_args()

    params = {
        "tecido": args.tecido if args.tecido in TECIDOS else None,
        "preset": args.preset,
        "compensacao": args.compensacao,
        "underlay": args.underlay,
        "maquina_id": args.maquina,
    }

    try:
        dst = route(args.arte, params, difficulty=args.dificuldade)
    except RuntimeError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2

    if args.out:
        os.replace(dst, args.out)
        dst = args.out

    metrics = StitchMetrics(dst)
    resultado = run_checklist(metrics, params)

    if args.json:
        payload = {
            "dst_gerado": dst,
            "params": params,
            **resultado,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if resultado["aprovado"] else 1

    print(f"=== STITCHGUARD PIPELINE (gerar -> validar -> otimizar) ===")
    print(f"DST gerado   : {dst}")
    print(f"Tecido       : {args.tecido} | Preset: {params['preset'] or '-'} | Compensacao: {params['compensacao'] or '-'} | Underlay: {params['underlay']}")
    print(f"Pontos       : {metrics.stitch_count} | Passo medio: {metrics.average_stitch_length_mm():.2f} mm")
    print(f"Saltos       : {len(metrics.jumps())} (max {metrics.max_jump_mm():.1f} mm)")
    print("---")
    for nome, r in resultado["itens"].items():
        estado = "OK" if r["score"] is not None and r["aprovado"] else ("REVISAO" if r["score"] is None else "FALHA")
        print(f"  [{estado:7s}] {nome:15s} score={r['score']} - {r['detalhe']}")
    print("---")
    print(f"SCORE GLOBAL : {resultado['score_global']} (min {0.85})")
    print(f"APROVADO     : {'SIM' if resultado['aprovado'] else 'NAO'}")
    otz = resultado.get("otimizacao_saltos")
    if otz:
        print(f"OTIMIZACAO   : saltos totais {otz['original']}mm -> {otz['otimizado']}mm (melhoria {otz['percentual']}%)")
    return 0 if resultado["aprovado"] else 1


if __name__ == "__main__":
    sys.exit(main())
