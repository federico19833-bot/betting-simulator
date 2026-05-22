import sqlite3
conn = sqlite3.connect('data/simulazione_betting.db')
c = conn.cursor()
c.execute("SELECT id, match, quota_reale, esito, profitto_netto FROM giocate WHERE match LIKE '%Slavia%'")
rows = c.fetchall()
if rows:
    for r in rows:
        print(f"#{r[0]} {r[1]} | Q{r[2]} | {r[3]} | {r[4]:+.2f}")
else:
    print("Non trovata nel DB")
conn.close()