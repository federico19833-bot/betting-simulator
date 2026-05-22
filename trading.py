from config import STAKE, COMMISSION_RATE, BETFAIR_APP_KEY, BETFAIR_USERNAME, BETFAIR_PASSWORD
from database import inserisci_giocata, aggiorna_esito, get_giocate_in_corso, get_giocata_by_match
import time
import re
import json

SIMULATED_DELAY_MINUTES = 60

SMARKETS = "https://api.smarkets.com/v3"
THESPORTSDB = "https://www.thesportsdb.com/api/v1/json/3"

def fetch_json(url):
    import requests
    try:
        r = requests.get(url, timeout=15)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_contracts(market_id):
    data = fetch_json(f"{SMARKETS}/markets/{market_id}/contracts/")
    return data.get("contracts", []) if data else []

def check_event_settled(event_id):
    data = fetch_json(f"{SMARKETS}/events/{event_id}/")
    if data:
        evs = data.get("events", [])
        if evs:
            state = evs[0].get("state", "")
            return state not in ("live", "inplay", "pre_match", "")
    return False

def check_sportsdb(match_name):
    import re, requests as _requests
    home_team, away_team = "", ""
    if " v " in match_name:
        home_team, away_team = match_name.split(" v ", 1)
    elif " vs " in match_name:
        home_team, away_team = match_name.split(" vs ", 1)
    
    clean_home = re.sub(r'\s*\((?:BRN|KSA|ECU|COL|CHI|URU|ARG)\)', '', home_team).strip()
    clean_away = re.sub(r'\s*\((?:BRN|KSA|ECU|COL|CHI|URU|ARG)\)', '', away_team).strip()
    
    searches = []
    if home_team and away_team:
        searches.append(f"{clean_home}_vs_{clean_away}".replace(" ", "_"))
        searches.append(f"{home_team}_vs_{away_team}".replace(" ", "_"))
        searches.append(f"{clean_home}_v_{clean_away}".replace(" ", "_"))
        searches.append(match_name.replace(" v ", "_vs_").replace(" ", "_"))
    
    for s in searches:
        data = fetch_json(f"{THESPORTSDB}/searchevents.php?e={s}")
        if data and data.get("event"):
            for ev in data["event"]:
                home = ev.get("intHomeScore")
                away = ev.get("intAwayScore")
                if home is not None and away is not None:
                    total = int(home) + int(away)
                    print(f"[TRADING] TheSportsDB: {match_name} -> {home}-{away} (tot: {total})")
                    return total >= 1
    
    for team in [clean_home, clean_away]:
        if not team:
            continue
        search_team = team.replace(" ", "_")
        r = _requests.get(f"{THESPORTSDB}/searchteams.php?t={search_team}", timeout=10)
        if r.status_code != 200:
            continue
        td = r.json()
        teams = td.get("teams") or []
        if not teams:
            continue
        tid = teams[0].get("idTeam", "")
        if not tid:
            continue
        last = fetch_json(f"{THESPORTSDB}/eventslast.php?id={tid}")
        if not last or not last.get("results"):
            continue
        for ev in last["results"]:
            h = ev.get("strHomeTeam", "")
            a = ev.get("strAwayTeam", "")
            if clean_home.lower() in h.lower() or clean_away.lower() in a.lower():
                hs = ev.get("intHomeScore")
                aws = ev.get("intAwayScore")
                if hs is not None and aws is not None:
                    total = int(hs) + int(aws)
                    print(f"[TRADING] TheSportsDB (last): {match_name} -> {hs}-{aws} (tot: {total})")
                    return total >= 1
    
    print(f"[TRADING] TheSportsDB: nessun risultato per {match_name}")
    return None

def execute_entry(match, campionato, volume, quota, event_id="", whale_max=0, whale_tot=0, open_date=""):
    existing = get_giocata_by_match(match, "IN_CORSO")
    if existing:
        print(f"[TRADING] SKIP {match}: gia in corso (#{existing['id']})")
        return None
    giocata_id = inserisci_giocata(match, campionato, volume, quota, event_id, whale_max, whale_tot, open_date)
    w = f" | Balena: {whale_max:.0f}€" if whale_max >= 10000 else ""
    print(f"[TRADING] GIOCATA ENTRATA #{giocata_id}: {match} | Quota {quota} | Stake {STAKE}€{w}")
    return giocata_id

def check_over_05_result(event_id):
    if not check_event_settled(event_id):
        return None
    markets = fetch_json(f"{SMARKETS}/events/{event_id}/markets/")
    if not markets:
        return None
    for m in markets.get("markets", []):
        mt = m.get("market_type", {})
        if isinstance(mt, dict) and mt.get("name") == "OVER_UNDER" and mt.get("param") == "0.5":
            mid = m.get("id")
            contracts = get_contracts(mid)
            for c in contracts:
                ct = c.get("contract_type", {})
                if isinstance(ct, dict) and ct.get("name") == "OVER":
                    state = c.get("state_or_outcome", "").lower()
                    if state in ("won", "winner"):
                        return True
                    elif state in ("lost", "loser"):
                        return False
                    return None
    return None

def check_betfair_result(market_id):
    import requests as _requests
    _session = requests.Session()
    r = _session.post(BF_LOGIN,
        data={"username": BETFAIR_USERNAME, "password": BETFAIR_PASSWORD},
        headers={"Accept": "application/json", "X-Application": BETFAIR_APP_KEY})
    data = r.json()
    if data.get("status") != "SUCCESS":
        print(f"[BF-CHECK] Login fallito")
        return None
    token = data["token"]
    headers = {
        "X-Application": BETFAIR_APP_KEY,
        "X-Authentication": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    try:
        r2 = _requests.post(f"{BF_API}/listMarketBook/", headers=headers,
            data=json.dumps({
                "marketIds": [market_id],
                "priceProjection": {"priceData": ["EX_BEST_OFFERS"]}
            }), timeout=15)
        if r2.status_code != 200:
            return None
        book = r2.json()
        if not book or not isinstance(book, list) or len(book) == 0:
            return None
        mkt = book[0]
        status = mkt.get("status", "")
        if status == "CLOSED":
            for runner in mkt.get("runners", []):
                if runner.get("selectionId") == 5851483:
                    rc = runner.get("status", "")
                    if rc == "WINNER":
                        print(f"[BF-CHECK] {market_id}: Over 0.5 WINNER")
                        return True
                    elif rc == "LOSER":
                        print(f"[BF-CHECK] {market_id}: Over 0.5 LOSER")
                        return False
            print(f"[BF-CHECK] {market_id}: CLOSED ma risultato non chiaro")
            return None
        print(f"[BF-CHECK] {market_id}: status={status}")
        return None
    except Exception as e:
        print(f"[BF-CHECK] Errore: {e}")
        return None

def resolve_match(giocata):
    quota_entry = giocata["quota_reale"]
    match = giocata["match"]
    is_win = None
    
    result = check_sportsdb(match)
    if result is not None:
        is_win = result
        print(f"[TRADING] TheSportsDB: {match} -> {'GOAL' if is_win else '0-0'}")
    
    if is_win is None:
        market_id = giocata.get("event_id", "")
        if market_id:
            bf_result = check_betfair_result(market_id)
            if bf_result is not None:
                is_win = bf_result
                print(f"[TRADING] Betfair: {match} -> {'GOAL' if is_win else '0-0'}")
    
    if is_win is None:
        print(f"[TRADING] Nessuna fonte per {match}, riprovo al prossimo scan")
        return None
    
    if is_win:
        gross_profit = STAKE * (quota_entry - 1)
        net_profit = gross_profit * (1 - COMMISSION_RATE)
        esito = "VINTA"
    else:
        net_profit = -STAKE
        esito = "PERSA"
    aggiorna_esito(giocata["id"], esito, net_profit)
    print(f"[TRADING] GIOCATA #{giocata['id']}: {esito} | Profitto netto: {net_profit:.2f}EUR")
    return {
        "id": giocata["id"],
        "match": giocata["match"],
        "campionato": giocata["campionato"],
        "quota": quota_entry,
        "esito": esito,
        "profitto": net_profit
    }

def check_and_resolve_pending():
    risolti = []
    in_corso = get_giocate_in_corso()
    for g in in_corso:
        from datetime import datetime
        orario = datetime.fromisoformat(g["orario"])
        elapsed = (datetime.now() - orario).total_seconds() / 60
        if elapsed >= SIMULATED_DELAY_MINUTES:
            res = resolve_match(g)
            if res:
                risolti.append(res)
    return risolti
