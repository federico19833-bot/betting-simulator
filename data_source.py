import json
import os
import time
import requests
from datetime import datetime
from config import VOLUME_THRESHOLD, MIN_ODDS, MAX_ODDS
from betfair_data import scan_over05_inplay
from selenium_query import get_realtime_over05 as selenium_check_quota

THESPORTSDB = "https://www.thesportsdb.com/api/v1/json/3"

def check_no_goal_yet(match_name):
    try:
        search = match_name.replace(" v ", "_").replace(" vs ", "_").replace(" ", "_")
        r = requests.get(f"{THESPORTSDB}/searchevents.php?e={search}", timeout=10)
        if r.status_code != 200:
            return True
        data = r.json()
        if not data or not data.get("event"):
            return True
        for ev in data["event"]:
            home = ev.get("intHomeScore")
            away = ev.get("intAwayScore")
            if home is not None and away is not None:
                total = int(home) + int(away)
                if total >= 1:
                    print(f"[PRE-ENTRY] GOL GIA SEGNATO: {match_name} {home}-{away} → SKIP")
                    return False
        return True
    except Exception as e:
        print(f"[PRE-ENTRY] Errore TheSportsDB per {match_name}: {e}")
        return True

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

        in_range = MIN_ODDS <= quota <= MAX_ODDS and volume >= VOLUME_THRESHOLD
        bf_event = {
            "match": match, "campionato": campionato,
            "volume": round(volume), "quota": quota,
            "in_range": in_range, "monitored": False,
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
                    if volume > t.get("best_volume", 0):
                        t["best_volume"] = volume

                    if not t.get("entered") and volume >= VOLUME_THRESHOLD:
                        realtime_quota = selenium_check_quota(market_id)
                        is_inplay = bf.get("_is_inplay", False)

                        if realtime_quota == -1:
                            print(f"[ENTRY SKIP] {match}: mercato sospeso (gol?), non entro")
                        elif realtime_quota is None:
                            print(f"[ENTRY SKIP] {match}: Selenium errore, SKIP per sicurezza")
                        elif realtime_quota == "NO_BACK_PRICES":
                            if is_inplay:
                                print(f"[ENTRY SKIP] {match}: IN-PLAY senza prezzi back, probabilmente gol")
                            else:
                                print(f"[WATCH] {match}: PRE-MATCH senza prezzi back, aspetto DevKey {quota}")
                        else:
                            t["last_price"] = realtime_quota
                            if realtime_quota < MIN_ODDS:
                                print(f"[WATCH] {match}: Selenium {realtime_quota} < {MIN_ODDS}, aspetto")
                            elif realtime_quota >= MAX_ODDS:
                                print(f"[RIMOSSO] {match}: Selenium {realtime_quota} >= {MAX_ODDS}")
                                tracked.pop(track_key, None)
                            elif MIN_ODDS <= realtime_quota < MAX_ODDS:
                                no_goal = check_no_goal_yet(match) if is_inplay else True
                                if not no_goal:
                                    print(f"[ENTRY SKIP] {match}: gol gia segnato, non entro")
                                else:
                                    risultati.append({
                                        "match": match, "campionato": campionato,
                                        "volume": t.get("best_volume", volume), "quota": realtime_quota,
                                        "event_id": market_id,
                                        "whale_max": 0, "whale_tot": 0,
                                        "source": "Betfair+Selenium",
                                        "open_date": bf.get("open_date", ""),
                                    })
                                    t["entered"] = True
                                    tipo = "PRE-MATCH" if not is_inplay else "IN-PLAY"
                                    print(f"[ENTRY {tipo}] a {realtime_quota} (DevKey: {quota}): {match} | Vol: {volume:.0f} EUR")

                    if quota >= MAX_ODDS and track_key in tracked:
                        tracked.pop(track_key, None)
                        print(f"[RIMOSSO] {match}: quota DevKey salita a {quota}")
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
                        "open_date": bf.get("open_date", ""),
                    }
                    tipo = "PRE-MATCH" if not is_inplay else "IN-PLAY"

    now = datetime.now()
    to_remove = []
    for k in list(tracked.keys()):
        t = tracked[k]
        if t.get("entered"):
            continue
        gone_from_scan = k.startswith("bf_") and k not in {f"bf_{m.get('market_id','')}" for m in betfair_matches.values()}
        if gone_from_scan:
            print(f"[TRACK] RIMOSSO: {t.get('match')} - non piu in live")
            to_remove.append(k)
        else:
            first_seen = t.get("first_seen", "")
            if first_seen:
                try:
                    elapsed = (now - datetime.fromisoformat(first_seen)).total_seconds() / 3600
                    if elapsed > 6:
                        print(f"[TRACK] SCADUTO: {t.get('match')} - tracciato da {elapsed:.1f}h senza entrare")
                        to_remove.append(k)
                except:
                    pass
    for k in to_remove:
        tracked.pop(k, None)

    save_tracking(tracked)
    
    # Sort by volume descending
    tutti_eventi.sort(key=lambda x: x["volume"], reverse=True)
    
    scan_file = os.path.join(os.path.dirname(__file__), "last_scan.json")
    with open(scan_file, "w", encoding="utf-8") as f:
        json.dump(tutti_eventi, f, ensure_ascii=False, indent=2)

    return risultati
