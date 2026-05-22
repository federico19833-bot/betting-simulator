import requests
import json
import time
from config import BETFAIR_APP_KEY, BETFAIR_USERNAME, BETFAIR_PASSWORD

BF_API = "https://api.betfair.it/exchange/betting/rest/v1.0"
BF_LOGIN = "https://identitysso.betfair.it/api/login"

_session = None
_token = None

def _login():
    global _session, _token
    _session = requests.Session()
    r = _session.post(BF_LOGIN,
        data={"username": BETFAIR_USERNAME, "password": BETFAIR_PASSWORD},
        headers={"Accept": "application/json", "X-Application": BETFAIR_APP_KEY})
    data = r.json()
    if data.get("status") == "SUCCESS":
        _token = data["token"]
        print(f"[BF-CHECK] Login OK")
        return True
    print(f"[BF-CHECK] Login fallito: {data}")
    return False

def _headers():
    if not _token:
        if not _login():
            return None
    return {
        "X-Application": BETFAIR_APP_KEY,
        "X-Authentication": _token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

def check_result_betfair(market_id):
    h = _headers()
    if not h:
        return None
    try:
        r = requests.post(f"{BF_API}/listMarketBook/", headers=h,
            data=json.dumps({
                "marketIds": [market_id],
                "priceProjection": {"priceData": ["EX_BEST_OFFERS"]}
            }), timeout=15)
        if r.status_code != 200:
            print(f"[BF-CHECK] Error: {r.status_code}")
            return None
        book = r.json()
        if not book or not isinstance(book, list) or len(book) == 0:
            return None
        
        mkt = book[0]
        status = mkt.get("status", "")
        
        if status == "CLOSED":
            runners = mkt.get("runners", [])
            for runner in runners:
                sid = runner.get("selectionId")
                if sid == 5851483:  # Over 0.5
                    rc = runner.get("status", "")
                    if rc == "WINNER":
                        print(f"[BF-CHECK] {market_id}: Over 0.5 WINNER -> VINTA")
                        return True
                    elif rc == "LOSER":
                        print(f"[BF-CHECK] {market_id}: Over 0.5 LOSER -> PERSA")
                        return False
            print(f"[BF-CHECK] {market_id}: CLOSED ma risultato non chiaro")
            return None
        
        if status == "SUSPENDED":
            print(f"[BF-CHECK] {market_id}: SUSPENDED (match in corso o gol)")
            return None
        
        print(f"[BF-CHECK] {market_id}: status={status}")
        return None
        
    except Exception as e:
        print(f"[BF-CHECK] Errore: {e}")
        return None

if __name__ == "__main__":
    _login()
    markets_to_check = [
        ("1.258390442", "BFC Daugavpils v Ogre United"),
        ("1.258438109", "Al Najma v Al-Ittihad"),
        ("1.258409992", "Al Arabi Kuwait v Al Tadhamon"),
        ("1.258438130", "Al Budaiya v Manama Club"),
    ]
    for mid, name in markets_to_check:
        result = check_result_betfair(mid)
        print(f"  {name}: {result}")