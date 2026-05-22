import sqlite3
import os
from datetime import datetime
from config import DB_PATH

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS giocate (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orario TEXT NOT NULL,
            match TEXT NOT NULL,
            campionato TEXT NOT NULL,
            volume_rilevato REAL NOT NULL,
            quota_reale REAL NOT NULL,
            esito TEXT NOT NULL DEFAULT 'IN_CORSO',
            profitto_netto REAL DEFAULT 0,
            event_id TEXT DEFAULT ''
        )
    """)
    try:
        conn.execute("ALTER TABLE giocate ADD COLUMN event_id TEXT DEFAULT ''")
    except:
        pass
    try:
        conn.execute("ALTER TABLE giocate ADD COLUMN whale_max REAL DEFAULT 0")
    except:
        pass
    try:
        conn.execute("ALTER TABLE giocate ADD COLUMN whale_tot REAL DEFAULT 0")
    except:
        pass
    try:
        conn.execute("ALTER TABLE giocate ADD COLUMN open_date TEXT DEFAULT ''")
    except:
        pass
    try:
        conn.execute("ALTER TABLE giocate ADD COLUMN risultato TEXT DEFAULT ''")
    except:
        pass
    conn.commit()
    conn.close()

def inserisci_giocata(match, campionato, volume, quota, event_id="", whale_max=0, whale_tot=0, open_date=""):
    conn = get_connection()
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO giocate (orario, match, campionato, volume_rilevato, quota_reale, esito, event_id, whale_max, whale_tot, open_date) VALUES (?, ?, ?, ?, ?, 'IN_CORSO', ?, ?, ?, ?)",
        (now, match, campionato, volume, quota, event_id, whale_max, whale_tot, open_date)
    )
    conn.commit()
    giocata_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return giocata_id

def aggiorna_esito(giocata_id, esito, profitto, risultato=""):
    conn = get_connection()
    conn.execute(
        "UPDATE giocate SET esito = ?, profitto_netto = ?, risultato = ? WHERE id = ?",
        (esito, round(profitto, 2), risultato, giocata_id)
    )
    conn.commit()
    conn.close()

def get_giocate_in_corso():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM giocate WHERE esito = 'IN_CORSO'").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_tutte_giocate():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM giocate ORDER BY orario DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_giocata_by_match(match, esito=None):
    conn = get_connection()
    if esito:
        rows = conn.execute("SELECT id FROM giocate WHERE match = ? AND esito = ? LIMIT 1", (match, esito)).fetchall()
    else:
        rows = conn.execute("SELECT id FROM giocate WHERE match = ? LIMIT 1", (match,)).fetchall()
    conn.close()
    return rows[0] if rows else None

def get_statistiche_giornaliere():
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT * FROM giocate WHERE orario LIKE ?",
        (f"{today}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
