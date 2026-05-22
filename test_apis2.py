import requests

# Try these real-time APIs:
# 1. Football-Data.org (need free API key)
# 2. API-Football via RapidAPI
# 3. Scorebat
# 4. Try Sofascore with different approach

# Try football-data.org with free tier - search matches
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Try live scores from various endpoints
tests = [
    ("https://api.football-data.org/v4/matches?status=LIVE", "football-data.org LIVE"),
    ("https://api.football-data.org/v4/matches?date=2026-05-21", "football-data.org today"),
    ("https://v3.football.api-sports.io/status", "API-Football status"),
]

for url, name in tests:
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"{name}: {r.status_code} | {r.text[:300]}")
    except Exception as e:
        print(f"{name}: {e}")

# Try v3.football.api-sports.io with free key
print("\n--- API-Football (v3) ---")
r = requests.get("https://v3.football.api-sports.io/timezone", headers=headers, timeout=10)
print(f"Timezone: {r.status_code} | {r.text[:200]}")

# Try fixtures endpoint (free tier allows some requests)
r = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers={**headers, 'x-apisports-key': 'free'}, timeout=10)
print(f"Fixtures live: {r.status_code} | {r.text[:300]}")

# Try mosaic / alternative real-time sources
print("\n--- Alternatives ---")
r = requests.get("https://www.goal.com/en-gb/live-scores", headers=headers, timeout=10)
print(f"Goal.com: {r.status_code} len={len(r.text)}")

# Try SofaScore Android API endpoint (different from web)
r = requests.get("https://api.sofascore.com/api/v1/sport/football/events/live", headers={
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
    'Accept': 'application/json',
}, timeout=10)
print(f"Sofascore mobile API: {r.status_code} | {r.text[:200]}")