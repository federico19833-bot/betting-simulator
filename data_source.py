import requests
import time
from config import VOLUME_THRESHOLD, MIN_ODDS, MAX_ODDS

SMARKETS = "https://api.smarkets.com/v3"

def fetch_json(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=15)
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
    under_id = None
    for c in (contracts.get("contracts") or contracts if isinstance(contracts, dict) else []):
        ct = c.get("contract_type", {})
        if isinstance(ct, dict) and ct.get("name") == "UNDER":
            under_id = c.get("id")
            break
    if not under_id:
        return 0, 0
    q = (quotes if isinstance(quotes, dict) else {}).get(str(under_id), {})
    if isinstance(q, dict):
        for bid in q.get("bids", []):
            price = float(bid.get("price", 0)) / 1000
            qty = float(bid.get("quantity", 0)) / 100
            if price > 0:
                return price, qty
    return 0, 0

def event_name(ev):
    h = (ev.get("home_team") or {}).get("name", "?")
    a = (ev.get("away_team") or {}).get("name", "?")
    return f"{h} vs {a}"

def scan_markets():
    risultati = []
    for state in ["live", "inplay"]:
        data = get_events(state)
        events = data.get("events", [])
        if events:
            break
    print(f"[SMARKETS] Trovati {len(events)} eventi LIVE")
    for ev in events[:30]:
        eid = ev.get("id")
        match = event_name(ev)
        comp = (ev.get("competition") or {}).get("name", "?")
        markets = get_markets(eid)
        mkt = None
        for m in (markets.get("markets") or markets if isinstance(markets, dict) else []):
            if isinstance(m, dict):
                mt = m.get("market_type", {})
                if isinstance(mt, dict) and mt.get("name") == "OVER_UNDER" and mt.get("param") == "0.5":
                    mkt = m
                    break
        if not mkt:
            time.sleep(0.2)
            continue
        mid = mkt.get("id")
        cids = get_contracts(mid)
        quotes = get_quotes(mid)
        best_price, volume = over_05_price(quotes, cids)
        if MIN_ODDS <= best_price <= MAX_ODDS and volume >= VOLUME_THRESHOLD:
            risultati.append({
                "match": match, "campionato": comp,
                "volume": volume, "quota": best_price, "event_id": eid,
            })
            print(f"[SMARKETS] LIVE segnale: {match} | Quota {best_price} | Volume {volume:.0f}€")
        time.sleep(0.3)
    return risultati
