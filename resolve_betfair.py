import sqlite3
from datetime import datetime
from config import STAKE, COMMISSION_RATE
from betfair_check_result import check_result_betfair

conn = sqlite3.connect("data/simulazione_betting.db")
c = conn.cursor()
c.execute("SELECT id, match, quota_reale, event_id, orario FROM giocate WHERE esito='IN_CORSO'")
rows = c.fetchall()
conn.close()

print(f"IN_CORSO: {len(rows)}")
for r in rows:
    gid, match, quota, event_id, orario = r
    dt = datetime.fromisoformat(orario)
    elapsed = (datetime.now() - dt).total_seconds() / 60
    print(f"\n#{gid} {match} | Quota {quota} | event_id={event_id} | {elapsed:.0f}min")
    
    if elapsed < 60:
        print(f"  Troppo recente")
        continue
    
    if event_id:
        result = check_result_betfair(event_id)
        if result is True:
            net = STAKE * (quota - 1) * (1 - COMMISSION_RATE)
            print(f"  -> VINTA +{net:.2f}EUR")
            conn2 = sqlite3.connect("data/simulazione_betting.db")
            conn2.execute("UPDATE giocate SET esito=?, profitto_netto=? WHERE id=?", ("VINTA", net, gid))
            conn2.commit()
            conn2.close()
        elif result is False:
            net = -STAKE
            print(f"  -> PERSA {net:.2f}EUR")
            conn2 = sqlite3.connect("data/simulazione_betting.db")
            conn2.execute("UPDATE giocate SET esito=?, profitto_netto=? WHERE id=?", ("PERSA", net, gid))
            conn2.commit()
            conn2.close()
        else:
            print(f"  -> Non risolto")
    else:
        print(f"  -> No event_id")