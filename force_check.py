import sqlite3
from datetime import datetime
from trading import check_sportsdb, resolve_match
from database import get_giocate_in_corso

in_corso = get_giocate_in_corso()
print(f"IN_CORSO: {len(in_corso)}")
now = datetime.now()

for g in in_corso:
    orario = datetime.fromisoformat(g["orario"])
    elapsed = (now - orario).total_seconds() / 60
    match = g["match"]
    print(f"\n#{g['id']} {match} | Quota {g['quota_reale']} | Entrato: {orario.strftime('%H:%M')} | {elapsed:.0f} min fa")
    
    if elapsed >= 5:
        result = check_sportsdb(match)
        print(f"  TheSportsDB: {result}")
    else:
        print(f"  Troppo recente ({elapsed:.0f} min)")