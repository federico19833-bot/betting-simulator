import sqlite3
from config import STAKE, COMMISSION_RATE

quota = 1.08
gross = STAKE * (quota - 1)
net = gross * (1 - COMMISSION_RATE)

conn = sqlite3.connect('data/simulazione_betting.db')
conn.execute("UPDATE giocate SET esito='VINTA', profitto_netto=? WHERE id=49", (round(net, 2),))
conn.commit()
c = conn.cursor()
c.execute("SELECT id, match, quota_reale, esito, profitto_netto FROM giocate WHERE id=49")
r = c.fetchone()
print(f"#{r[0]} {r[1]} | Q{r[2]} | {r[3]} | {r[4]:+.2f}")
conn.close()