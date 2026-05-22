import requests
import time
from datetime import datetime

ODDS_API = "https://api.the-odds-api.com/v4"
API_KEY = None

def init(api_key):
    global API_KEY
    API_KEY = api_key

def get_over05_odds():
    if not API_KEY:
        return []
    try:
        r = requests.get(f"{ODDS_API}/sports/upcoming/odds", params={
            "apiKey": API_KEY, "regions": "eu", "markets": "totals", "oddsFormat": "decimal"
        }, timeout=10)
        if r.status_code != 200:
            print(f"[ODDSAPI] Errore {r.status_code}")
            return []
        
        data = r.json()
        remaining = r.headers.get("x-requests-remaining", "?")
        risultati = []
        
        for match in data:
            home = match.get("home_team", "")
            away = match.get("away_team", "")
            match_name = f"{home} vs {away}"
            commence = match.get("commence_time", "")
            sport = match.get("sport_key", "soccer")
            league = sport.replace("soccer_", "").replace("_", " ").title() if "soccer" in sport else sport
            
            # Check if match is live (commence_time in the past)
            is_live = False
            if commence:
                try:
                    from datetime import datetime, timezone
                    ct = datetime.fromisoformat(commence.replace("Z", "+00:00"))
                    is_live = ct < datetime.now(timezone.utc)
                except:
                    pass
            
            if not is_live:
                continue
            
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market.get("key") == "totals":
                        for outcome in market.get("outcomes", []):
                            name = outcome.get("name", "")
                            point = outcome.get("point", "")
                            if "Over" in name and point == 0.5:
                                price = outcome.get("price", 0)
                                risultati.append({
                                    "match": match_name,
                                    "league": league,
                                    "quota": price,
                                    "bookmaker": bookmaker.get("title", "?"),
                                    "last_update": bookmaker.get("last_update", ""),
                                })
                            break
                    break
                break
        
        if risultati:
            # Group by match, take best odds
            best = {}
            for r in risultati:
                key = r["match"]
                if key not in best or r["quota"] < best[key]["quota"]:
                    best[key] = r
            print(f"[ODDSAPI] {len(best)} partite live con Over 0.5 | {remaining} richieste rimaste")
            return list(best.values())
        
        print(f"[ODDSAPI] Nessuna partita live con Over 0.5 | {remaining} richieste rimaste")
        return []
    except Exception as e:
        print(f"[ODDSAPI] Errore: {e}")
        return []

if __name__ == "__main__":
    from config import ODDSAPI_KEY
    init(ODDSAPI_KEY)
    odds = get_over05_odds()
    for o in odds[:5]:
        print(f"  {o['match'][:40]:40s} quota={o['quota']:.3f} ({o['bookmaker']})")
