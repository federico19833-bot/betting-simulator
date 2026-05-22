import requests, re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}

# Try flashscore API - they have a WebSocket but also some REST endpoints
# Try livescore.com
print("--- Livescore.com ---")
try:
    r = requests.get('https://www.livescore.com/en/football/live/', headers=headers, timeout=10)
    print(f"Status: {r.status_code}, Length: {len(r.text)}")
except Exception as e:
    print(f"Error: {e}")

# Try soccerway
print("\n--- Soccerway ---")
try:
    r = requests.get('https://int.soccerway.com/matches/live/', headers=headers, timeout=10)
    print(f"Status: {r.status_code}, Length: {len(r.text)}")
except Exception as e:
    print(f"Error: {e}")

# Try Sofascore with different approach - use their widget/embed
print("\n--- Sofascore widget ---")
try:
    r = requests.get('https://widgets.sofascore.com/widgets/match-list/classic', headers=headers, timeout=10)
    print(f"Status: {r.status_code}, Length: {len(r.text)}")
except Exception as e:
    print(f"Error: {e}")

# Try ESPN API
print("\n--- ESPN API ---")
try:
    r = requests.get('http://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard', headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    d = r.json()
    events = d.get('events', [])
    for ev in events[:3]:
        name = ev.get('name', '?')
        status = ev.get('status', {}).get('type', {}).get('description', '')
        scores = ev.get('competitions', [{}])[0].get('scores', [])
        print(f"  {name} [{status}] {scores}")
except Exception as e:
    print(f"Error: {e}")

# Try ESPN live scores for all soccer
print("\n--- ESPN All Soccer Live ---")
try:
    r = requests.get('http://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard', headers=headers, timeout=10)
    d = r.json()
    events = d.get('events', [])
    print(f"Events: {len(events)}")
    for ev in events[:5]:
        name = ev.get('name', '?')
        status = ev.get('status', {}).get('type', {}).get('description', '')
        comps = ev.get('competitions', [{}])
        scores = comps[0].get('scores', []) if comps else []
        home_score = scores[0].get('value', '?') if len(scores) > 0 else '?'
        away_score = scores[1].get('value', '?') if len(scores) > 1 else '?'
        print(f"  {name} [{status}] {home_score}-{away_score}")
except Exception as e:
    print(f"Error: {e}")