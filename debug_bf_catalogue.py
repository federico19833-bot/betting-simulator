import requests, json

s = requests.Session()
r = s.post("https://identitysso.betfair.it/api/login",
    data={"username": "federico1983@hotmail.it", "password": "Fedeele86."},
    headers={"Accept": "application/json", "X-Application": "69ELmrb2twFe9hus"})
t = r.json()["token"]
h = {"X-Application": "69ELmrb2twFe9hus", "X-Authentication": t,
     "Accept": "application/json", "Content-Type": "application/json"}

# Get catalogue with marketTypes filter
cat = requests.post("https://api.betfair.it/exchange/betting/rest/v1.0/listMarketCatalogue/",
    headers=h, data=json.dumps({
        "filter": {"eventTypeIds": ["1"], "inPlayOnly": True,
                   "marketTypes": ["OVER_UNDER_0_5"]},
        "marketProjection": ["EVENT", "RUNNER_DESCRIPTION", "COMPETITION"],
        "maxResults": 200
    }), timeout=15)

data = cat.json()
print(f"Found {len(data)} markets")
for m in data[:20]:
    event = m.get("event", {}).get("name", "?")
    mid = m.get("marketId", "?")
    runners = [r.get("runnerName") for r in m.get("runners", [])]
    print(f"  {event} | ID={mid} | runners={runners}")

# Check if specific matches are there
print("\n--- Looking for specific matches ---")
for m in data:
    event = m.get("event", {}).get("name", "")
    if any(x in event.lower() for x in ["bournemouth", "genk", "monza", "hapoel"]):
        print(f"  {event} | ID={m.get('marketId')}")
