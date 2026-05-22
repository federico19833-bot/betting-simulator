import sqlite3, os
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "simulazione_betting.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, match, quota_reale, esito, orario FROM giocate WHERE esito = 'IN_CORSO'")
for r in c.fetchall():
    print(f"#{r[0]} {r[1]} | Quota: {r[2]} | {r[3]} | {r[4]}")
conn.close()