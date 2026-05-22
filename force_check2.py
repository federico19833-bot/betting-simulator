import sqlite3
from datetime import datetime
from trading import check_sportsdb
from database import get_giocate_in_corso

in_corso = get_giocate_in_corso()
now = datetime.now()

for g in in_corso[:5]:
    orario = datetime.fromisoformat(g["orario"])
    elapsed = (now - orario).total_seconds() / 60
    match = g["match"]
    print(f"\n#{g['id']} {match} | Quota {g['quota_reale']} | {elapsed:.0f} min fa")
    
    if elapsed >= 60:
        result = check_sportsdb(match)
        print(f"  Result: {result}")
    else:
        print(f"  Troppo recente")