import sqlite3
from datetime import datetime
from trading import check_sportsdb, resolve_match
from database import get_giocate_in_corso, aggiorna_esito
from config import STAKE, COMMISSION_RATE
from betfair_check_result import check_result_betfair

in_corso = get_giocate_in_corso()
now = datetime.now()

for g in in_corso:
    orario = datetime.fromisoformat(g["orario"])
    elapsed = (now - orario).total_seconds() / 60
    match = g["match"]
    mid = g.get("event_id", "")
    quota = g["quota_reale"]
    
    if elapsed < 60:
        print(f"#{g['id']} {match} | Troppo recente ({elapsed:.0f} min)")
        continue
    
    # Try TheSportsDB first
    result = check_sportsdb(match)
    if result is not None:
        if result:
            net = STAKE * (quota - 1) * (1 - COMMISSION_RATE)
            esito = "VINTA"
        else:
            net = -STAKE
            esito = "PERSA"
        aggiorna_esito(g["id"], esito, net)
        print(f"#{g['id']} {match} | {esito} (TheSportsDB) | {net:+.2f}EUR")
        continue
    
    # Fallback: Betfair market status
    if mid:
        result = check_result_betfair(mid)
        if result is not None:
            if result:
                net = STAKE * (quota - 1) * (1 - COMMISSION_RATE)
                esito = "VINTA"
            else:
                net = -STAKE
                esito = "PERSA"
            aggiorna_esito(g["id"], esito, net)
            print(f"#{g['id']} {match} | {esito} (Betfair) | {net:+.2f}EUR")
            continue
    
    print(f"#{g['id']} {match} | NON RISOLTO")