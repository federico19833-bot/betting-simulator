import json, os, sys, subprocess, threading
from datetime import datetime, timezone, timedelta
from database import get_tutte_giocate, get_giocate_in_corso
from config import DB_PATH, MIN_ODDS, MAX_ODDS, VOLUME_THRESHOLD, STAKE, POLL_INTERVAL_SECONDS, INITIAL_BALANCE

CET = timezone(timedelta(hours=1))
CEST = timezone(timedelta(hours=2))

def to_italian(utc_str):
    if not utc_str:
        return ""
    try:
        if "Z" in utc_str:
            dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        elif "+" in utc_str[10:]:
            dt = datetime.fromisoformat(utc_str)
        else:
            return utc_str
        dt_it = dt.astimezone(CEST if dt.month >= 4 and dt.month <= 10 else CET)
        return dt_it.strftime("%Y-%m-%d %H:%M")
    except:
        return utc_str

DATA_FILE = os.path.join(os.path.dirname(__file__), "docs", "data.json")
LAST_HASH_FILE = os.path.join(os.path.dirname(__file__), "last_data_hash.txt")

def data_hash(data):
    return str(hash(json.dumps(data, ensure_ascii=False)))

GIT = r"C:\Program Files\Git\bin\git.exe"

def deploy_github():
    def _deploy():
        try:
            repo = os.path.dirname(__file__)
            subprocess.run([GIT, "add", "docs/data.json"], cwd=repo, capture_output=True, text=True, timeout=15)
            subprocess.run([GIT, "commit", "-m", "update dashboard data", "--allow-empty"], cwd=repo, capture_output=True, text=True, timeout=15)
            subprocess.run([GIT, "push", "origin", "main"], cwd=repo, capture_output=True, text=True, timeout=30)
            print("[DASHBOARD] GitHub Pages aggiornato")
        except Exception as e:
            print(f"[DASHBOARD] Errore push: {e}")
    threading.Thread(target=_deploy, daemon=True).start()

def generate(deploy=False):
    giocate = get_tutte_giocate()
    stats = {"total": 0, "wins": 0, "losses": 0, "in_corso": 0, "winrate": 0, "profit": 0.0, "roi": 0.0, "balance": INITIAL_BALANCE}
    if giocate:
        wins = sum(1 for g in giocate if g["esito"] == "VINTA")
        losses = sum(1 for g in giocate if g["esito"] == "PERSA")
        incorso = sum(1 for g in giocate if g["esito"] == "IN_CORSO")
        total = len(giocate)
        profit = sum(g["profitto_netto"] for g in giocate)
        wr = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        roi = (profit / (total * STAKE) * 100) if total > 0 else 0
        stats = {"total": total, "wins": wins, "losses": losses, "in_corso": incorso, "winrate": round(wr, 1), "profit": round(profit, 2), "roi": round(roi, 2), "balance": round(INITIAL_BALANCE + profit, 2)}
    
    giocate_list = []
    for g in giocate:
        giocate_list.append({
            "id": g["id"],
            "orario": g["orario"][:19].replace("T", " "),
            "match": g["match"],
            "campionato": g["campionato"],
            "quota": g["quota_reale"],
            "volume": round(g["volume_rilevato"]),
            "esito": g["esito"],
            "profitto": g["profitto_netto"],
            "risultato": g.get("risultato", ""),
            "risultato_ht": g.get("risultato_ht", ""),
            "whale_max": g.get("whale_max", 0),
            "whale_tot": g.get("whale_tot", 0)
        })
    
    live_events = []
    scan_file = os.path.join(os.path.dirname(__file__), "last_scan.json")
    if os.path.exists(scan_file):
        with open(scan_file, "r", encoding="utf-8") as f:
            live_events = json.load(f)
        for ev in live_events:
            ev["open_date"] = to_italian(ev.get("open_date", ""))
    
    tracked_matches = []
    track_file = os.path.join(os.path.dirname(__file__), "tracked_matches.json")
    if os.path.exists(track_file):
        with open(track_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for eid, t in raw.items():
            tracked_matches.append({
                "event_id": eid,
                "match": t.get("match", "?"),
                "campionato": t.get("campionato", "?"),
                "open_date": to_italian(t.get("open_date", "")),
                "quota_attuale": t.get("last_price", 0),
                "quota_iniziale": t.get("first_price", 0),
                "volume": round(t.get("volume", 0)),
                "best_volume": round(t.get("best_volume", 0)),
                "whale_max": round(t.get("whale_max", 0)),
                "entered": t.get("entered", False),
            })
    
    data = {
        "last_update": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "config": {
            "min_odds": MIN_ODDS,
            "max_odds": MAX_ODDS,
            "volume_threshold": VOLUME_THRESHOLD,
            "stake": STAKE,
            "poll_interval": POLL_INTERVAL_SECONDS
        },
        "stats": stats,
        "live_events": live_events,
        "tracked_matches": tracked_matches,
        "giocate": giocate_list,
        "max_whale": max([e.get("whale_max", 0) or 0 for e in live_events], default=0)
    }
    
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    h = data_hash(data)
    changed = True
    if os.path.exists(LAST_HASH_FILE):
        with open(LAST_HASH_FILE, "r") as f:
            changed = f.read().strip() != h
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(LAST_HASH_FILE, "w") as f:
        f.write(h)
    
    print(f"[DASHBOARD] data.json {'(cambiato)' if changed else '(invariato)'} - {stats['total']} giocate, {len(live_events)} eventi live")
    
    if deploy and changed:
        deploy_github()
    
    return changed

if __name__ == "__main__":
    generate(deploy="--deploy" in sys.argv)
