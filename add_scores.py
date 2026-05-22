import sqlite3
from trading import check_sportsdb, check_betfair_result

conn = sqlite3.connect('data/simulazione_betting.db')
c = conn.cursor()
c.execute("SELECT id, match, esito, event_id FROM giocate WHERE esito != 'IN_CORSO' AND (risultato IS NULL OR risultato = '')")
rows = c.fetchall()
print(f"Trovate {len(rows)} giocate senza risultato")

for r in rows:
    gid, match, esito, event_id = r
    result, score = check_sportsdb(match)
    if score:
        conn.execute("UPDATE giocate SET risultato=? WHERE id=?", (score, gid))
        print(f"#{gid} {match}: {esito} {score}")
    elif event_id and result is not None:
        bf_result = check_betfair_result(event_id)
        if bf_result is not None:
            score = "1-0" if bf_result else "0-0"
            conn.execute("UPDATE giocate SET risultato=? WHERE id=?", (score, gid))
            print(f"#{gid} {match}: {esito} {score} (Betfair)")
    else:
        print(f"#{gid} {match}: nessun risultato")

# Mark PERSA without score as 0-0
c.execute("UPDATE giocate SET risultato='0-0' WHERE esito='PERSA' AND (risultato IS NULL OR risultato = '')")
conn.commit()

# Show remaining
c.execute("SELECT id, match, esito, risultato FROM giocate ORDER BY id DESC LIMIT 20")
print("\nUltime 20 giocate:")
for r in c.fetchall():
    print(f"#{r[0]} {r[1][:40]} | {r[2]} | {r[3]}")

conn.close()