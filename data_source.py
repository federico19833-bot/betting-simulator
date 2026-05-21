import json
import os
import time
from datetime import datetime
from config import VOLUME_THRESHOLD, MIN_ODDS, MAX_ODDS
from betfair_data import scan_over05_inplay

TRACK_FILE = os.path.join(os.path.dirname(__file__), "tracked_matches.json")
WATCH_MIN = 1.01
WATCH_MAX = 1.10

def load_tracking():
    if os.path.exists(TRACK_FILE):
        try:
            with open(TRACK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_tracking(tracked):
    with open(TRACK_FILE, "w", encoding="utf-8") as f:
        json.dump(tracked, f, ensure_ascii=False, indent=2)

def scan_markets():
    risultati = []
    tracked = load_tracking()
    tutti_eventi = []

    betfair_matches = {}
    try:
        bf_results = scan_over05_inplay()
        for bf in bf_results:
            match = bf["match"]
            betfair_matches[match] = bf
        print(f"[BETFAIR] Trovati {len(betfair_matches)} eventi totali")
    except Exception as e:
        print(f"[BETFAIR] Errore scan: {e}")

    for match, bf in betfair_matches.items():
        quota = bf["quota"]
        volume = bf["volume"]
        campionato = bf["campionato"]
        market_id = bf.get("market_id", "")
        event_id = bf.get("event_id", "")

        bf_event = {
            "match": match, "campionato": campionato,
            "volume": round(volume), "quota": quota,
            "in_range": False, "monitored": False,
            "whale_max": 0, "whale_tot": 0,
            "source": "Betfair", "event_id": event_id, "market_id": market_id,
            "_is_inplay": bf.get("_is_inplay", False),
            "open_date": bf.get("open_date", ""),
        }
        tutti_eventi.append(bf_event)

        track_key = f"bf_{market_id}"

        if WATCH_MIN <= quota <= WATCH_MAX:
                # Always watch if in range, volume check only for entry
                if track_key in tracked:
                    t = tracked[track_key]
                    prev = t.get("last_price", 0)
                    t["last_price"] = quota
                    t["volume"] = volume
                    # Remember best volume ever seen
                    if volume > t.get("best_volume", 0):
                        t["best_volume"] = volume

                    # Entry: current volume >= threshold OR best volume ever seen >= threshold
                    has_volume = volume >= VOLUME_THRESHOLD or t.get("best_volume", 0) >= VOLUME_THRESHOLD
                    if not t.get("entered") and quota >= MIN_ODDS and quota <= MAX_ODDS and has_volume:
                            risultati.append({
                                "match": match, "campionato": campionato,
                                "volume": volume, "quota": quota,
                                "event_id": market_id,
                                "whale_max": 0, "whale_tot": 0,
                                "source": "Betfair",
                            })
                            t["entered"] = True
                            tipo = "PRE-MATCH" if not bf.get("_is_inplay") else "IN-PLAY"
                            print(f"[ENTRY {tipo}] a {quota}: {match} | Vol: {volume:.0f} EUR")

                    if quota > MAX_ODDS:
                        tracked.pop(track_key, None)
                        print(f"[RIMOSSO] {match}: quota salita a {quota}")
                else:
                    is_inplay = bf.get("_is_inplay", False)
                    tracked[track_key] = {
                        "match": match, "campionato": campionato,
                        "first_price": quota, "last_price": quota,
                        "volume": volume, "best_volume": volume,
                        "whale_max": 0, "whale_tot": 0,
                        "entered": False,
                        "first_seen": datetime.now().isoformat(),
                        "source": "Betfair",
                        "is_inplay": is_inplay,
                    }
                    tipo = "PRE-MATCH" if not is_inplay else "IN-PLAY"

    to_remove = [k for k in tracked if k.startswith("bf_") and k not in {f"bf_{m.get('market_id','')}" for m in betfair_matches.values()}]
    for k in to_remove:
        if not tracked[k].get("entered"):
            print(f"[BETFAIR] PERSO: {tracked[k].get('match')} - non piu in live")
        tracked.pop(k, None)

    save_tracking(tracked)
    
    # Sort by volume descending
    tutti_eventi.sort(key=lambda x: x["volume"], reverse=True)
    
    scan_file = os.path.join(os.path.dirname(__file__), "last_scan.json")
    with open(scan_file, "w", encoding="utf-8") as f:
        json.dump(tutti_eventi, f, ensure_ascii=False, indent=2)

    return risultati
