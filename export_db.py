import sqlite3, os, shutil
from datetime import datetime

db_path = "data/simulazione_betting.db"

# Backup
backup_dir = "data/backups"
os.makedirs(backup_dir, exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"giocate_{ts}.db")
shutil.copy2(db_path, backup_path)
print(f"Backup salvato: {backup_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM giocate")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM giocate WHERE esito='VINTA'")
vinte = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM giocate WHERE esito='PERSA'")
perse = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM giocate WHERE esito='IN_CORSO'")
in_corso = c.fetchone()[0]
c.execute("SELECT SUM(profitto_netto) FROM giocate")
profitto = c.fetchone()[0] or 0

print(f"\n{'='*80}")
print(f"TOTALE: {total} | VINTE: {vinte} | PERSE: {perse} | IN_CORSO: {in_corso}")
print(f"PROFITTO NETTO: {profitto:+.2f} EUR")
print(f"WIN RATE: {vinte/(vinte+perse)*100:.1f}%" if (vinte+perse) > 0 else "")
print(f"{'='*80}\n")

c.execute("SELECT id, orario, match, campionato, quota_reale, volume_rilevato, esito, profitto_netto FROM giocate ORDER BY id")
for r in c.fetchall():
    print(f"#{r[0]:2d} | {r[1][:16]} | {r[2]:40s} | {r[3]:30s} | Q{r[4]} | V{r[5]:.0f} | {r[6]:8s} | {r[7]:+.2f}")

# Also export to CSV
import csv
csv_path = os.path.join(backup_dir, f"giocate_{ts}.csv")
c.execute("SELECT id, orario, match, campionato, quota_reale, volume_rilevato, esito, profitto_netto, event_id FROM giocate ORDER BY id")
rows = c.fetchall()
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "orario", "match", "campionato", "quota_reale", "volume_rilevato", "esito", "profitto_netto", "event_id"])
    writer.writerows(rows)
print(f"\nCSV esportato: {csv_path}")

conn.close()