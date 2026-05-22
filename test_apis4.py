import requests

headers = {'User-Agent': 'Mozilla/5.0'}

# ESPN leagues for soccer
leagues = [
    ("eng.1", "Premier League"),
    ("esp.1", "La Liga"),
    ("ita.1", "Serie A"),
    ("ger.1", "Bundesliga"),
    ("fra.1", "Ligue 1"),
    ("ued.1", "Champions League"),
    ("ued.2", "Europa League"),
    ("por.1", "Liga Portugal"),
    ("ned.1", "Eredivisie"),
    ("den.1", "Danish Superliga"),
    ("gre.1", "Greek Super League"),
    ("ukr.1", "Ukrainian Premier"),
    ("ind.1", "Indian Super League"),
    ("asn.1", "AFC"),
    ("fifa.world", "World Cup/Internationals"),
]

# Check which ones have data
for league_id, league_name in leagues:
    try:
        r = requests.get(f'http://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard', headers=headers, timeout=5)
        if r.status_code == 200:
            d = r.json()
            events = d.get('events', [])
            live = sum(1 for e in events if e.get('status',{}).get('type',{}).get('description','') not in ['Full Time','Postponed','Canceled',''])
            print(f"  {league_id:15s} {league_name:25s} -> {len(events)} events, {live} possible live")
        else:
            print(f"  {league_id:15s} {league_name:25s} -> {r.status_code}")
    except:
        print(f"  {league_id:15s} {league_name:25s} -> ERROR")

# Now search for our specific matches
print("\n--- Search for our matches ---")
searches = ["Rigas", "Daugavpils", "Ajax", "Odisha", "Brondby"]
for q in searches:
    try:
        r = requests.get(f'http://site.api.espn.com/apis/site/v2/sports/soccer/search?query={q}', headers=headers, timeout=5)
        if r.status_code == 200:
            d = r.json()
            print(f"  {q}: {list(d.keys())[:5]}")
        else:
            print(f"  {q}: {r.status_code}")
    except Exception as e:
        print(f"  {q}: {e}")