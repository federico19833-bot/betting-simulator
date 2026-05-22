import requests, json

s = requests.Session()
r = s.post("https://identitysso.betfair.it/api/login",
    data={"username": "federico1983@hotmail.it", "password": "Fedeele86."},
    headers={"Accept": "application/json", "X-Application": "69ELmrb2twFe9hus"})
t = r.json()["token"]
h = {"X-Application": "69ELmrb2twFe9hus", "X-Authentication": t,
     "Accept": "application/json", "Content-Type": "application/json"}

# Check Bournemouth and Genk Over 0.5 markets specifically
for mid, name in [("1.258188498", "Bournemouth v Man City"), ("1.258276405", "Genk v Antwerp")]:
    print(f"\n=== {name} (ID: {mid}) ===")
    
    # Get catalogue to check runner names
    cat = requests.post("https://api.betfair.it/exchange/betting/rest/v1.0/listMarketCatalogue/",
        headers=h, data=json.dumps({
            "filter": {"marketIds": [mid]},
            "marketProjection": ["RUNNER_DESCRIPTION"],
            "maxResults": 1
        }), timeout=15)
    
    if cat.status_code == 200 and len(cat.json()) > 0:
        m = cat.json()[0]
        print(f"Market name: {m.get('marketName')}")
        for r in m.get("runners", []):
            print(f"  Runner: {r.get('runnerName')} (ID: {r.get('selectionId')})")
    
    # Get market book
    book = requests.post("https://api.betfair.it/exchange/betting/rest/v1.0/listMarketBook/",
        headers=h, data=json.dumps({
            "marketIds": [mid],
            "priceProjection": {"priceData": ["EX_BEST_OFFERS", "EX_ALL_OFFERS"], "side": "BACK"}
        }), timeout=15)
    
    if book.status_code == 200 and len(book.json()) > 0:
        b = book.json()[0]
        print(f"Status: {b.get('status')}")
        print(f"TotalMatched: {b.get('totalMatched')}")
        print(f"TotalAvailable: {b.get('totalAvailable')}")
        for r in b.get("runners", []):
            sid = r.get("selectionId")
            back = r.get("ex", {}).get("availableToBack", [])
            print(f"  Runner {sid}: {back}")
