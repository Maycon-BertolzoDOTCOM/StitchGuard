"""StitchGuard - Interface de linha de comando do validador."""
import argparse
import json
import sys
from domain.maquinas import get_maquina, listar_maquinas, formatar_maquina
from .metrics import StitchMetrics
from .checklist import run_checklist


def main():
    parser = argparse.ArgumentParser(prog="stitchguard", description="Validador de matrizes de bordado (checklist de 11 itens).")
    parser.add_argument("arquivo", help="Caminho do arquivo de bordado (.dst, .pes, .exp...)")
    parser.add_argument("--tecido", choices=["malha", "jeans", "nylon", "bone", "cetim"], default=None)
    parser.add_argument("--preset", choices=["ralo", "padrao", "denso"], default=None, help="Variante do dial p/ cetim (ralo|padrao|denso)")
    parser.add_argument("--compensacao", choices=["alta", "media", "baixa"], default=None)
    parser.add_argument("--underlay", action="store_true")
    parser.add_argument("--maquina", default=None, help=f"ID da maquina: {', '.join(listar_maquinas())} (padrao: generica)")
    parser.add_argument("--json", action="store_true", help="Saida em JSON (via stdout)")
    args = parser.parse_args()

    try:
        metrics = StitchMetrics(args.arquivo)
    except Exception as exc:
        print(f"ERRO: nao foi possivel ler '{args.arquivo}': {exc}", file=sys.stderr)
        return 2

    params = {
        "tecido": args.tecido,
        "preset": args.preset,
        "compensacao": args.compensacao,
        "underlay": args.underlay,
        "maquina_id": args.maquina,
    }
    resultado = run_checklist(metrics, params)

    maquina = get_maquina(args.maquina)
    if args.maquina and maquina["maquina_id"] != args.maquina:
        print(f"AVISO: Maquina '{args.maquina}' nao encontrada. Usando fallback '{maquina['maquina_id']}'.", file=sys.stderr)

    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0 if resultado["aprovado"] else 1

    print(f"Arquivo      : {args.arquivo}")
    print(f"Maquina      : {formatar_maquina(maquina)}")
    print(f"Dimensoes    : {metrics.width_mm:.1f} x {metrics.height_mm:.1f} mm")
    print(f"Pontos       : {metrics.stitch_count}")
    print(f"Pontos/cm2   : {metrics.density_stitches_per_cm()}")
    print(f"Saltos       : {len(metrics.jumps())} (max {metrics.max_jump_mm():.1f} mm)")
    print(f"Paradas      : {metrics.stops()} | Trocas de cor: {metrics.color_breaks}")
    print("---")
    for nome, r in resultado["itens"].items():
        estado = "OK" if r["score"] is not None and r["aprovado"] else ("REVISAO" if r["score"] is None else "FALHA")
        print(f"  [{estado:7s}] {nome:15s} score={r['score']} - {r['detalhe']}")
    print("---")
    print(f"SCORE GLOBAL : {resultado['score_global']} (min {0.85})")
    print(f"APROVADO     : {'SIM' if resultado['aprovado'] else 'NAO'}")
    if resultado["itens_pendentes_revisao_humana"]:
        print(f"REVISAO HUMANA PENDENTE: {', '.join(resultado['itens_pendentes_revisao_humana'])}")
    otz = resultado.get("otimizacao_saltos")
    if otz:
        print(f"OTIMIZACAO   : saltos totais {otz['original']}mm -> {otz['otimizado']}mm (melhoria {otz['percentual']}%)")
    return 0 if resultado["aprovado"] else 1


if __name__ == "__main__":
    sys.exit(main())
