import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from database import get_tutte_giocate
from config import INITIAL_BALANCE, EQUITY_CHART_PATH, COMMISSION_RATE, STAKE
import os

def calculate_equity():
    giocate = get_tutte_giocate()
    if not giocate:
        return None, None, 0, 0
    df = pd.DataFrame(giocate[::-1])
    df["profitto_netto"] = df["profitto_netto"].astype(float)
    balance = INITIAL_BALANCE
    equity = []
    for _, row in df.iterrows():
        balance += row["profitto_netto"]
        equity.append(balance)
    df["equity"] = equity
    total_profit = df["profitto_netto"].sum()
    total_staked = len(df) * STAKE
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
    return df, total_profit, roi

def generate_equity_chart():
    df, total_profit, roi = calculate_equity()
    if df is None:
        print("[ANALISI] Nessuna giocata registrata.")
        return None
    os.makedirs(os.path.dirname(EQUITY_CHART_PATH), exist_ok=True)
    plt.figure(figsize=(12, 6))
    plt.plot(df["equity"], color="#2563eb", linewidth=2, label="Equity")
    plt.axhline(y=INITIAL_BALANCE, color="gray", linestyle="--", alpha=0.5, label=f"Capitale iniziale ({INITIAL_BALANCE}€)")
    plt.fill_between(range(len(df)), INITIAL_BALANCE, df["equity"], where=(df["equity"] >= INITIAL_BALANCE), color="#22c55e", alpha=0.15)
    plt.fill_between(range(len(df)), df["equity"], INITIAL_BALANCE, where=(df["equity"] < INITIAL_BALANCE), color="#ef4444", alpha=0.15)
    wins = len(df[df["esito"] == "VINTA"])
    losses = len(df[df["esito"] == "PERSA"])
    in_corso = len(df[df["esito"] == "IN_CORSO"])
    winrate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    plt.title(f"Equity Curve - Strategia 1.05\nROI: {roi:.2f}% | Giocate: {len(df)} | WR: {winrate:.1f}% | Profitto: {total_profit:.2f}€", fontsize=13, fontweight="bold")
    plt.xlabel("Giocata #")
    plt.ylabel("Capitale (€)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(EQUITY_CHART_PATH, dpi=150)
    plt.close()
    print(f"[ANALISI] Grafico salvato: {EQUITY_CHART_PATH}")
    return EQUITY_CHART_PATH
