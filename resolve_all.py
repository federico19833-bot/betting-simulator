import sqlite3
from datetime import datetime
from trading import check_sportsdb, resolve_match
from database import get_giocate_in_corso, aggiorna_esito
from config import STAKE, COMMISSION_RATE

in_corso = get_giocate_in_corso()
now = datetime.now()

for g in in_corso:
    orario = datetime.fromisoformat(g["orario"])
    elapsed = (now - orario).total_seconds() / 60
    match = g["match"]
    
    if elapsed < 60:
        print(f"#{g['id']} {match} | Troppo recente ({elapsed:.0f} min)")
        continue
    
    result = check_sportsdb(match)
    if result is None:
        print(f"#{g['id']} {match} | Nessun risultato")
        continue
    
    quota = g["quota_reale"]
    if result:
        gross = STAKE * (quota - 1)
        net = gross * (1 - COMMISSION_RATE)
        esito = "VINTA"
    else:
        net = -STAKE
        esito = "PERSA"
    
    aggiorna_esito(g["id"], esito, net)
    print(f"#{g['id']} {match} | {esito} | Quota {quota} | {net:+.2f}EUR")