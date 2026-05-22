import sqlite3
conn = sqlite3.connect('data/simulazione_betting.db')
c = conn.cursor()
c.execute("SELECT id, match, quota_reale, esito, profitto_netto, orario FROM giocate WHERE date(orario) >= '2026-05-21' ORDER BY id")
rows = c.fetchall()
for r in rows:
    print(f"#{r[0]:2d} | {r[1]:40s} | Quota {r[2]} | {r[3]:8s} | {r[4]:+.2f}EUR | {r[5][:16]}")
conn.close()