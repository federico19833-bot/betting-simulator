import requests, json

s = requests.Session()
r = s.post("https://identitysso.betfair.it/api/login",
    data={"username": "federico1983@hotmail.it", "password": "Fedeele86."},
    headers={"Accept": "application/json", "X-Application": "69ELmrb2twFe9hus"})
t = r.json()["token"]
h = {"X-Application": "69ELmrb2twFe9hus", "X-Authentication": t,
     "Accept": "application/json", "Content-Type": "application/json"}

# Get ALL in-play soccer markets to find Bournemouth
cat = requests.post("https://api.betfair.it/exchange/betting/rest/v1.0/listMarketCatalogue/",
    headers=h, data=json.dumps({
        "filter": {"eventTypeIds": ["1"], "inPlayOnly": True},
        "marketProjection": ["EVENT"],
        "maxResults": 200
    }), timeout=15)

if cat.status_code == 200:
    data = cat.json()
    # Find Bournemouth mentions
    for m in data:
        event = m.get("event", {}).get("name", "")
        name = m.get("marketName", "")
        if "bournemouth" in event.lower() or "man city" in event.lower():
            print(f"MATCH: {event} | Market: {name} | ID: {m.get('marketId')}")
    
    # Count total and Over/Under 0.5
    ou05 = [m for m in data if "Over/Under 0.5 Goals" in m.get("marketName", "")]
    print(f"\nTOT Over/Under 0.5 trovati: {len(ou05)}")
    for m in ou05:
        print(f"  - {m.get('event', {}).get('name')} (ID: {m.get('marketId')})")
else:
    print(f"Error: {cat.status_code}")
    print(cat.text[:500])
