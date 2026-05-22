import requests, json

s = requests.Session()
r = s.post("https://identitysso.betfair.it/api/login",
    data={"username": "federico1983@hotmail.it", "password": "Fedeele86."},
    headers={"Accept": "application/json", "X-Application": "69ELmrb2twFe9hus"})
t = r.json()["token"]
h = {"X-Application": "69ELmrb2twFe9hus", "X-Authentication": t,
     "Accept": "application/json", "Content-Type": "application/json"}

# Get Bournemouth Over 0.5 market book
r2 = requests.post("https://api.betfair.it/exchange/betting/rest/v1.0/listMarketBook/",
    headers=h, data=json.dumps({
        "marketIds": ["1.258188498"],
        "priceProjection": {"priceData": ["EX_BEST_OFFERS", "EX_ALL_OFFERS"], "side": "BACK"}
    }))
book = r2.json()[0]
print("Status:", book.get("status"))
print("Total Matched:", book.get("totalMatched"))
print("Total Available:", book.get("totalAvailable"))
print("Delayed:", book.get("isMarketDataDelayed"))
print("In Play:", book.get("inplay"))
for r in book.get("runners", []):
    ex = r.get("ex", {})
    back = ex.get("availableToBack", [])
    sid = r.get("selectionId")
    print(f"\nRunner {sid}:")
    if back:
        print(f"  BACK prices: {back}")
    else:
        print(f"  No back prices")
