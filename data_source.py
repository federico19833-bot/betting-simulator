import requests
import time
import json
import os
from datetime import datetime
from config import VOLUME_THRESHOLD, MIN_ODDS, MAX_ODDS
from smarkets_ws import get_ws

SMARKETS = "https://api.smarkets.com/v3"
WATCH_MIN = 1.01
WATCH_MAX = 1.09
TRACK_FILE = os.path.join(os.path.dirname(__file__), "tracked_matches.json")

def fetch_json(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_events(state="live"):
    return fetch_json(f"{SMARKETS}/events/", params={
        "type": "football_match", "state": state, "limit": 50
    }) or {}

def get_markets(event_id):
    return fetch_json(f"{SMARKETS}/events/{event_id}/markets/") or {}

def get_contracts(market_id):
    return fetch_json(f"{SMARKETS}/markets/{market_id}/contracts/") or {}

def get_quotes(market_id):
    return fetch_json(f"{SMARKETS}/markets/{market_id}/quotes/") or {}

def over_05_price(quotes, contracts):
    over_id = None
    for c in (contracts.get("contracts") or contracts if isinstance(contracts, dict) else []):
        ct = c.get("contract_type", {})
        if isinstance(ct, dict) and ct.get("name") == "OVER":
            over_id = c.get("id")
            break
    if not over_id:
        return 0, 0
    q = (quotes if isinstance(quotes, dict) else {}).get(str(over_id), {})
    if isinstance(q, dict):
        for bid in q.get("bids", []):
            price = float(bid.get("price", 0)) / 1000
            qty = float(bid.get("quantity", 0)) / 100
            if price > 0:
                return price, qty
    return 0, 0

def whale_detection(quotes, contracts, min_price=1.01, max_price=1.09):
    """Trova i grossi investitori (balene) nel book dell'Over 0.5"""
    over_id = None
    for c in (contracts.get("contracts") or contracts if isinstance(contracts, dict) else []):
        ct = c.get("contract_type", {})
        if isinstance(ct, dict) and ct.get("name") == "OVER":
            over_id = c.get("id")
            break
    if not over_id:
        return 0, 0, []
    
    q = (quotes if isinstance(quotes, dict) else {}).get(str(over_id), {})
    bids = q.get("bids", []) if isinstance(q, dict) else []
    
    livelli = []
    max_singolo = 0
    totale = 0
    for bid in bids:
        price = float(bid.get("price", 0)) / 1000
        qty = float(bid.get("quantity", 0)) / 100
        if min_price <= price <= max_price and qty > 0:
            livelli.append({"quota": round(price, 3), "volume": round(qty)})
            if qty > max_singolo:
                max_singolo = qty
            totale += qty
    
    return round(max_singolo), round(totale), livelli

def event_name(ev):
    return ev.get("name", "Partita sconosciuta")

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
    tutti_eventi = []
    tracked = load_tracking()
    live_ids = set()
    
    for state in ["live", "inplay"]:
        data = get_events(state)
        events = data.get("events", [])
        if events:
            break
    print(f"[SMARKETS] Trovati {len(events)} eventi LIVE")
    
    for ev in events[:15]:
        eid = ev.get("id")
        live_ids.add(eid)
        match = event_name(ev)
        slug = ev.get("full_slug", "")
        parts = slug.split("/")
        comp = parts[3].replace("-", " ").title() if len(parts) > 3 else "?"
        markets = get_markets(eid)
        mkt = None
        for m in (markets.get("markets") or markets if isinstance(markets, dict) else []):
            if isinstance(m, dict):
                mt = m.get("market_type", {})
                if isinstance(mt, dict) and mt.get("name") == "OVER_UNDER" and mt.get("param") == "0.5":
                    mkt = m
                    break
        if not mkt:
            time.sleep(0.1)
            continue
        mid = mkt.get("id")
        cids = get_contracts(mid)
        quotes = get_quotes(mid)
        best_price, volume = over_05_price(quotes, cids)
        whale_max, whale_tot, whale_livelli = whale_detection(quotes, cids, 1.01, 1.09)
        whale_flag = " 🐋" if whale_max >= 15000 else ""
        
        # Subscribe market to WebSocket for real-time whale detection
        try:
            ws = get_ws()
            ws.subscribe(mid, "")
            ws_whale = ws.get_last_whale()
            if ws_whale and ws_whale["market_id"] == mid and ws_whale["importo"] > whale_max:
                whale_max = ws_whale["importo"]
                whale_flag = " 🐋"
                if "whale_ws" not in tracked.get(eid, {}):
                    print(f"[WS] BALENA CONFERMATA: {ws_whale['importo']:.0f}€ a quota {ws_whale['quota']} per {match}")
                    ws.clear_whale()
        except:
            pass
        
        if volume > 0 and best_price < 1.20:
            tutti_eventi.append({
                "match": match, "campionato": comp,
                "volume": round(volume), "quota": best_price,
                "in_range": False, "monitored": eid in tracked,
                "whale_max": whale_max, "whale_tot": whale_tot,
            })
        
        # TRACKING LOGIC: watch matches from 1.01-1.09, enter at >= 1.09
        if best_price < 1.50 and volume >= VOLUME_THRESHOLD:
            if eid in tracked:
                # Already watching this match
                t = tracked[eid]
                prev = t.get("last_price", 0)
                t["last_price"] = best_price
                t["volume"] = volume
                if whale_max > t.get("whale_max", 0):
                    t["whale_max"] = whale_max
                if whale_tot > t.get("whale_tot", 0):
                    t["whale_tot"] = whale_tot
                
                # Enter if odds crossed 1.09 (was below, now at or above)
                if not t.get("entered") and best_price >= MIN_ODDS and best_price <= MAX_ODDS:
                    if prev < MIN_ODDS:
                        risultati.append({
                            "match": match, "campionato": comp,
                            "volume": volume, "quota": best_price, "event_id": eid,
                            "whale_max": whale_max, "whale_tot": whale_tot,
                        })
                        t["entered"] = True
                        w = f" | Balena: {whale_max:.0f}€" if whale_max >= 10000 else ""
                        print(f"[SMARKETS] ENTRY a {best_price}{whale_flag}: {match} | Vol: {volume:.0f}€{w}")
                
                # Stop watching if odds went too high without entry
                if best_price > MAX_ODDS:
                    tracked.pop(eid, None)
                    print(f"[SMARKETS] RIMOSSO {match}: quota salita a {best_price} senza entry")
            else:
                # New match: start watching if odds in 1.01-1.09
                if WATCH_MIN <= best_price <= WATCH_MAX:
                    tracked[eid] = {
                        "match": match, "campionato": comp,
                        "first_price": best_price, "last_price": best_price,
                        "volume": volume, "whale_max": whale_max, "whale_tot": whale_tot,
                        "entered": False,
                        "first_seen": datetime.now().isoformat()
                    }
                    if whale_max >= 15000:
                        print(f"[SMARKETS] MONITORAGGIO{whale_flag}: {match} a {best_price} | Vol: {volume:.0f}€ | Balena {whale_max:.0f}€ a quote 1.01-1.09")
                    else:
                        print(f"[SMARKETS] MONITORAGGIO: {match} a {best_price} | Vol: {volume:.0f}€")
        
        time.sleep(0.1)
    
    # Clean up: remove tracked events no longer live
    to_remove = [eid for eid in tracked if eid not in live_ids]
    for eid in to_remove:
        if not tracked[eid].get("entered"):
            print(f"[SMARKETS] PERSO: {tracked[eid].get('match')} - non piu in live")
        tracked.pop(eid, None)
    
    save_tracking(tracked)
    
    scan_file = os.path.join(os.path.dirname(__file__), "last_scan.json")
    with open(scan_file, "w", encoding="utf-8") as f:
        json.dump(tutti_eventi, f, ensure_ascii=False, indent=2)
    
    return risultati
