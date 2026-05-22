import requests

# Try odds API - often less restricted
urls_to_try = [
    ("https://www.thesportsdb.com/api/v1/json/3/searchevents.php?e=Ajax_v_FC_Groningen", "TheSportsDB search"),
    ("https://www.thesportsdb.com/api/v1/json/3/livescore.php?s=Soccer", "TheSportsDB livescore"),
    ("https://api.openligadb.de/getmatchdata/bl1", "OpenLigaDB"),
    ("https://api.openligadb.de/getmatchdata/bl1/2026/18", "OpenLigaDB round"),
]

for url, name in urls_to_try:
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        print(f"{name}: {r.status_code} | {r.text[:200]}")
    except Exception as e:
        print(f"{name}: ERROR {e}")

# Try TheSportsDB live scores specifically
print("\n--- TheSportsDB live scores ---")
r = requests.get("https://www.thesportsdb.com/api/v1/json/3/latestscore.php?s=Soccer", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    events = d.get('events', d.get('match', []))
    if events:
        for ev in events[:5]:
            h = ev.get('strHomeTeam', '?')
            a = ev.get('strAwayTeam', '?')
            hs = ev.get('intHomeScore', '')
            as_ = ev.get('strAwayScore', '')
            status = ev.get('strStatus', '')
            print(f"  {h} {hs}-{as_} {a} [{status}]")
    else:
        print("No live events found, keys:", list(d.keys()))