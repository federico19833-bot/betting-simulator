import requests
import json
import time
from config import BETFAIR_APP_KEY, BETFAIR_USERNAME, BETFAIR_PASSWORD, VOLUME_THRESHOLD

BF_API = "https://api.betfair.it/exchange/betting/rest/v1.0"
BF_LOGIN = "https://identitysso.betfair.it/api/login"

_session = None
_token = None
_last_login = 0

def _login():
    global _session, _token, _last_login
    if _session and _token and time.time() - _last_login < 120:
        return _session, _token
    
    _session = requests.Session()
    r = _session.post(BF_LOGIN,
        data={"username": BETFAIR_USERNAME, "password": BETFAIR_PASSWORD},
        headers={"Accept": "application/json", "X-Application": BETFAIR_APP_KEY})
    data = r.json()
    if data.get("status") == "SUCCESS":
        _token = data["token"]
        _last_login = time.time()
        print(f"[BETFAIR] Login OK (token expires ~20min)")
        return _session, _token
    else:
        print(f"[BETFAIR] Login fallito: {data}")
        return None, None

def _headers():
    s, t = _login()
    if not s or not t:
        return None
    return {
        "X-Application": BETFAIR_APP_KEY,
        "X-Authentication": t,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

def _api_call(endpoint, payload):
    h = _headers()
    if not h:
        return None
    try:
        r = requests.post(f"{BF_API}/{endpoint}",
            headers=h, data=json.dumps(payload), timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"[BETFAIR] API error {endpoint}: {r.status_code} {r.text[:200]}")
            return None
    except Exception as e:
        print(f"[BETFAIR] Request error: {e}")
        return None

def scan_over05_inplay():
    """Scansiona tutti i mercati Over/Under 0.5 (pre-match + in-play) su Betfair"""
    headers = _headers()
    if not headers:
        return []
    
    ou05_markets = []
    
    # Step 1a: Get in-play soccer market catalogues
    inplay = _api_call("listMarketCatalogue/", {
        "filter": {"eventTypeIds": ["1"], "inPlayOnly": True},
        "marketProjection": ["EVENT", "RUNNER_DESCRIPTION", "COMPETITION"],
        "maxResults": 500
    })
    if inplay and isinstance(inplay, list):
        for m in inplay:
            if "Over/Under 0.5 Goals" in m.get("marketName", ""):
                m["_is_inplay"] = True
                ou05_markets.append(m)
    
    # Step 1b: Get pre-match soccer market catalogues
    prematch = _api_call("listMarketCatalogue/", {
        "filter": {"eventTypeIds": ["1"], "inPlayOnly": False},
        "marketProjection": ["EVENT", "RUNNER_DESCRIPTION", "COMPETITION"],
        "maxResults": 500,
        "sort": "FIRST_TO_START"
    })
    if prematch and isinstance(prematch, list):
        for m in prematch:
            if "Over/Under 0.5 Goals" in m.get("marketName", ""):
                m["_is_inplay"] = False
                ou05_markets.append(m)
    
    if not ou05_markets:
        return []
    
    total_inplay = sum(1 for m in ou05_markets if m.get("_is_inplay"))
    print(f"[BETFAIR] Trovati {len(ou05_markets)} mercati Over/Under 0.5 ({total_inplay} in-play, {len(ou05_markets)-total_inplay} pre-match)")
    
    results = []
    
    # Step 2: Get market book for prices (max 10 per call)
    for i in range(0, len(ou05_markets), 10):
        batch = ou05_markets[i:i+10]
        market_ids = [m["marketId"] for m in batch]
        
        book = _api_call("listMarketBook/", {
            "marketIds": market_ids,
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS", "EX_ALL_OFFERS"],
                "side": "BACK"
            }
        })
        
        if not book or not isinstance(book, list):
            continue
        
        for j, mkt in enumerate(batch):
            if j >= len(book):
                break
            
            book_data = book[j]
            event = mkt.get("event", {})
            comp = mkt.get("competition", {})
            
            match_name = event.get("name", "?")
            comp_name = comp.get("name", "?")
            market_id = mkt.get("marketId", "")
            total_matched = book_data.get("totalMatched", 0)
            total_available = book_data.get("totalAvailable", 0)
            is_delayed = book_data.get("isMarketDataDelayed", False)
            status = book_data.get("status", "")
            
            # Get Over 0.5 selection ID from catalogue runners
            over_id = None
            for runner in mkt.get("runners", []):
                if runner.get("runnerName") == "Over 0.5 Goals":
                    over_id = runner.get("selectionId")
                    break
            
            if not over_id:
                continue
            
            # Find Over 0.5 runner in book data
            over_price = 0
            over_liquidity = 0
            runners = book_data.get("runners", [])
            
            for runner in runners:
                if runner.get("selectionId") != over_id:
                    continue
                ex = runner.get("ex", {})
                back_prices = ex.get("availableToBack", [])
                
                if back_prices:
                    over_price = 0
                    over_liquidity = 0
                    for bp in back_prices:
                        p = bp.get("price", 0)
                        s = bp.get("size", 0)
                        if p > over_price and s >= VOLUME_THRESHOLD:
                            over_price = p
                            over_liquidity = s
                    if over_price == 0 and back_prices:
                        over_price = back_prices[0].get("price", 0)
                        over_liquidity = back_prices[0].get("size", 0)
                break
            
            if over_price > 0:
                results.append({
                    "match": match_name,
                    "campionato": comp_name,
                    "volume": round(over_liquidity),
                    "quota": over_price,
                    "market_id": market_id,
                    "event_id": event.get("id", ""),
                    "open_date": event.get("openDate", ""),
                    "total_matched": round(total_matched, 2),
                    "total_available": round(total_available, 2),
                    "is_delayed": is_delayed,
                    "status": status,
                    "source": "Betfair",
                    "_is_inplay": mkt.get("_is_inplay", False),
                })
    
    return results
