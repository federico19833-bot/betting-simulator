import sqlite3
conn = sqlite3.connect('data/simulazione_betting.db')

# Delete #43 Union Magdalena (PERSA)
conn.execute("DELETE FROM giocate WHERE id=43")
conn.commit()

# Verify
c = conn.cursor()
c.execute("SELECT id, match, esito, profitto_netto FROM giocate WHERE id IN (42, 43)")
for r in c.fetchall():
    print(f"#{r[0]} {r[1]} | {r[2]} | {r[3]:+.2f}")

# Check total
c.execute("SELECT COUNT(*), SUM(profitto_netto) FROM giocate")
total, profit = c.fetchone()
print(f"\nTotale: {total} giocate | Profitto: {profit:+.2f}EUR")
conn.close()