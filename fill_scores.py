import sqlite3

conn = sqlite3.connect('data/simulazione_betting.db')
c = conn.cursor()

# All PERSA are 0-0 (no goal)
c.execute("UPDATE giocate SET risultato='0-0' WHERE esito='PERSA' AND (risultato IS NULL OR risultato = '')")
print(f"PERSA aggiornate: {c.rowcount}")

# VINTA that we know scores for
known = {
    1: "0-1", 2: "1-0", 3: "1-0", 4: "2-0", 5: "1-0",
    6: "1-0", 7: "0-0", 8: "1-0", 9: "1-0", 10: "1-0",
    11: "1-0", 12: "1-0", 14: "1-0", 15: "1-0", 19: "1-0",
    23: "0-3", 24: "0-0",
    25: "1-0", 26: "1-0", 27: "1-0", 28: "1-0", 29: "1-0",
    30: "0-0", 31: "1-0", 32: "1-0", 33: "6-0", 34: "1-3",
    35: "1-0", 36: "1-0", 37: "2-1", 38: "1-0", 39: "1-0",
    40: "6-1", 41: "1-0", 42: "3-0", 44: "1-0",
    45: "0-0", 46: "0-0", 47: "1-0", 48: "1-0", 49: "2-0",
}

for gid, score in known.items():
    conn.execute("UPDATE giocate SET risultato=? WHERE id=?", (score, gid))

conn.commit()

# Show all
c.execute("SELECT id, match, esito, risultato FROM giocate ORDER BY id DESC")
for r in c.fetchall():
    print(f"#{r[0]:2d} {r[1][:40]:40s} | {r[2]:8s} | {r[3]}")

conn.close()