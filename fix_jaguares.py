import sqlite3
from config import STAKE, COMMISSION_RATE

conn = sqlite3.connect('data/simulazione_betting.db')

# Fix #42 Jaguares - VINTA
quota = 1.09
net = STAKE * (quota - 1) * (1 - COMMISSION_RATE)
conn.execute("UPDATE giocate SET esito='VINTA', profitto_netto=? WHERE id=42", (round(net, 2),))
conn.commit()

c = conn.cursor()
c.execute("SELECT id, match, quota_reale, esito, profitto_netto FROM giocate WHERE id IN (42, 43)")
for r in c.fetchall():
    print(f"#{r[0]} {r[1]} | Q{r[2]} | {r[3]} | {r[4]:+.2f}")
conn.close()