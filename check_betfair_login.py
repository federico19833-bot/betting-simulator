import requests
import json

APP_KEY = "69ELmrb2twFe9hus"

s = requests.Session()
r = s.post("https://identitysso.betfair.it/api/login",
    data={"username": "federico1983@hotmail.it", "password": "Fedeele86."},
    headers={"Accept": "application/json", "X-Application": APP_KEY})
token = r.json()["token"]

headers = {
    "X-Application": APP_KEY,
    "X-Authentication": token,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

market_ids = ["1.258055899", "1.258295510"]

for mid in market_ids:
    print(f"\n=== Market {mid} ===")
    r2 = requests.post("https://api.betfair.it/exchange/betting/rest/v1.0/listMarketBook/",
        headers=headers,
        data=json.dumps({
            "marketIds": [mid],
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS", "EX_ALL_OFFERS", "EX_TRADED"],
                "side": "BACK"
            }
        }),
        timeout=15)
    
    data = r2.json()
    if isinstance(data, list) and len(data) > 0:
        book = data[0]
        print(f"  Status: {book.get('status')}")
        print(f"  In-Play: {book.get('inPlay')}")
        print(f"  Raw JSON: {json.dumps(book, indent=2)[:2000]}")
    else:
        print(f"  Error: {data}")
