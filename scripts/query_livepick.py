#!/usr/bin/env python3
"""Query precomputed LivePick probabilities from the signal sheet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOOKUP = ROOT / "docs" / "livepick_lookup.json"
PARTITE = ROOT / "docs" / "livepick_partite.json"


def pct(x: float | None) -> str:
    if x is None:
        return "n/d"
    return f"{x:.1%}"


def show_agg(title: str, a: dict | None) -> None:
    print(f"\n{title}")
    if not a or not a.get("n"):
        print("  nessun campione")
        return
    print(
        f"  n={a['n']}  altro gol {a['altro_gol']}/{a['n']} = {pct(a['p_altro_gol'])}"
        f"  (IC95 {pct(a['ic95_low'])}–{pct(a['ic95_high'])})"
    )
    print(
        f"  gol medi dopo={a['e_gol_dopo']:.2f}  P(0)={pct(a['p_0'])}"
        f"  P(1)={pct(a['p_1'])}  P(2+)={pct(a['p_2plus'])}"
    )
    print(f"  minuto segnale medio={a.get('avg_minuto', 0):.1f}  lambda/min={a.get('lambda_min', 0):.4f}")


def main() -> None:
    p = argparse.ArgumentParser(description="Probabilità di un altro gol dal segnale LivePick")
    p.add_argument("--paese", help="es. India")
    p.add_argument("--campionato", help="es. India Super League")
    p.add_argument("--minuto", type=int, help="minuto del segnale, es. 64")
    p.add_argument("--risultato", help="risultato al segnale, es. 2-1")
    p.add_argument("--ora", type=int, help="minuto attuale, per P residua Poisson (es. 81)")
    args = p.parse_args()

    lookup = json.loads(LOOKUP.read_text(encoding="utf-8"))
    risultato = (args.risultato or "").replace(" ", "").replace("–", "-")

    if args.campionato:
        camp = lookup["campionati"].get(args.campionato)
        show_agg(f"Campionato {args.campionato} (tutti i segnali)", camp)
        if camp and args.minuto is not None:
            show_agg(f"Campionato {args.campionato} @ {args.minuto}'", camp.get("per_minuto", {}).get(str(args.minuto)))
        return

    if args.paese:
        pdata = lookup["paesi"].get(args.paese)
        if not pdata:
            keys = [k for k in lookup["paesi"] if args.paese.lower() in k.lower()]
            print("Paese non trovato.", f"Simili: {keys[:12]}" if keys else "")
            return
        show_agg(f"{args.paese} — tutti i segnali", pdata)
        if args.minuto is not None:
            show_agg(f"{args.paese} — segnale al {args.minuto}'", pdata["per_minuto"].get(str(args.minuto)))
        if risultato:
            show_agg(f"{args.paese} — risultato {risultato}", pdata["per_risultato"].get(risultato))
        if args.minuto is not None and risultato:
            key = f"{args.minuto}|{risultato}"
            show_agg(f"{args.paese} — {args.minuto}' e {risultato}", pdata["per_minuto_risultato"].get(key))
        if args.ora is not None:
            block = pdata["p_da_minuto"].get(str(args.ora))
            if block:
                print(f"\n{args.paese} — da minuto attuale {args.ora}' (Poisson, non empirico)")
                print(f"  P(altro gol al 90') = {pct(block['p_90'])}  E={block['e_gol_90']:.2f}")
                print(f"  P(altro gol al 90'+3') = {pct(block['p_90_3'])}  E={block['e_gol_90_3']:.2f}")
            else:
                lam = pdata.get("lambda_min_tardi") or pdata.get("lambda_min") or 0
                remain = max(90 - args.ora, 0)
                import math

                p90 = 1 - math.exp(-lam * remain)
                p3 = 1 - math.exp(-lam * (remain + 3))
                print(f"\n{args.paese} — da minuto attuale {args.ora}' (Poisson interpolato)")
                print(f"  P(90')={pct(p90)}  P(90'+3')={pct(p3)}")
        return

    g = lookup["globale"]
    show_agg("Globale — tutti i segnali", g)
    if args.minuto is not None:
        show_agg(f"Globale — segnale al {args.minuto}'", g["per_minuto"].get(str(args.minuto)))
    if risultato:
        show_agg(f"Globale — risultato {risultato}", g["per_risultato"].get(risultato))
    if args.ora is not None:
        block = g["p_da_minuto"].get(str(args.ora))
        if block:
            print(f"\nGlobale — da minuto attuale {args.ora}'")
            print(f"  P(90')={pct(block['p_90'])}  P(90'+3')={pct(block['p_90_3'])}")


if __name__ == "__main__":
    main()
