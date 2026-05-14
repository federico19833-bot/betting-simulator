import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, inserisci_giocata, aggiorna_esito, get_tutte_giocate
from analysis import calculate_equity, generate_equity_chart
from config import INITIAL_BALANCE
import random

CAMPIONATI = [
    ("Manchester Utd vs Liverpool", "Premier League"),
    ("Barcellona vs Real Madrid", "La Liga"),
    ("Juventus vs Inter", "Serie A"),
    ("Bayern vs Dortmund", "Bundesliga"),
    ("PSG vs Marseille", "Ligue 1"),
    ("Ajax vs Feyenoord", "Eredivisie"),
    ("Benfica vs Porto", "Primeira Liga"),
    ("Celtic vs Rangers", "Scottish Premiership"),
    ("Galatasaray vs Fenerbahce", "Super Lig"),
    ("Club Brugge vs Anderlecht", "Pro League"),
]

def genera_giocata(match, campionato, volume, quota, esito, profitto):
    gid = inserisci_giocata(match, campionato, volume, quota)
    aggiorna_esito(gid, esito, profitto)
    return gid

def run_demo():
    print("=" * 50)
    print("  DEMO SIMULAZIONE - Strategia 1.05")
    print("=" * 50)
    init_db()
    print("[DEMO] Pulizia dati precedenti...")
    import sqlite3
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM giocate")
    conn.commit()
    conn.close()
    print("[DEMO] Generazione 50 giocate simulate...")
    wins = 0
    total = 50
    for i in range(total):
        match, camp = CAMPIONATI[i % len(CAMPIONATI)]
        match = match.replace(" vs ", " vs ")
        camp = camp
        volume = random.randint(5000, 50000)
        quota = round(random.uniform(1.03, 1.06), 2)
        is_win = random.random() < 0.65
        if is_win:
            profitto = round(100 * (1.05 - 1) * 0.95, 2)
            esito = "VINTA"
            wins += 1
        else:
            profitto = -100.0
            esito = "PERSA"
        genera_giocata(match, camp, volume, quota, esito, profitto)
        print(f"  #{i+1}: {match} | {esito} | {profitto:+.2f}€")
    df, total_profit, roi = calculate_equity()
    print(f"\n[DEMO] RISULTATI:")
    print(f"  Giocate: {total}")
    print(f"  Vinte: {wins}")
    print(f"  Perse: {total - wins}")
    print(f"  Win Rate: {wins/total*100:.1f}%")
    print(f"  Profitto totale: {total_profit:.2f}€")
    print(f"  ROI: {roi:.2f}%")
    print(f"  Capitale finale: {INITIAL_BALANCE + total_profit:.2f}€")
    chart = generate_equity_chart()
    if chart:
        print(f"  Grafico salvato: {chart}")
    print("\n[DEMO] Completata! Guarda reports/andamento_strategia.png")

if __name__ == "__main__":
    run_demo()
