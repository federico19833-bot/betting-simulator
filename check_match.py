import requests, json
s = requests.Session()
r = s.post("https://identitysso.betfair.it/api/login",
    data={"username": "federico1983@hotmail.it", "password": "Fedeele86."},
    headers={"Accept": "application/json", "X-Application": "69ELmrb2twFe9hus"})
t = r.json()["token"]
h = {"X-Application": "69ELmrb2twFe9hus", "X-Authentication": t,
     "Accept": "application/json", "Content-Type": "application/json"}
r2 = requests.post("https://api.betfair.it/exchange/betting/rest/v1.0/listMarketBook/",
    headers=h, data=json.dumps({"marketIds": ["1.258248147"],
    "priceProjection": {"priceData": ["EX_BEST_OFFERS", "EX_ALL_OFFERS"], "side": "BACK"}}))
b = r2.json()[0]
print("Status:", b.get("status"))
print("Total Matched:", b.get("totalMatched"))
print("Total Available:", b.get("totalAvailable"))
print("Delayed:", b.get("isMarketDataDelayed"))
for runner in b.get("runners", []):
    sid = runner["selectionId"]
    back = runner["ex"].get("availableToBack", [])
    lay = runner["ex"].get("availableToLay", [])
    print(f"  Runner {sid}: back={back}, lay={lay}")
