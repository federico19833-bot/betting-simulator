from config import STAKE, COMMISSION_RATE
from database import inserisci_giocata, aggiorna_esito, get_giocate_in_corso, get_giocata_by_match
import time
import re

SIMULATED_DELAY_MINUTES = 180

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
    search = match_name.replace(" vs ", "_").replace(" ", "_")
    data = fetch_json(f"{THESPORTSDB}/searchevents.php?e={search}")
    if data and data.get("event"):
        for ev in data["event"]:
            home = ev.get("intHomeScore")
            away = ev.get("intAwayScore")
            if home is not None and away is not None:
                total = int(home) + int(away)
                print(f"[TRADING] TheSportsDB: {match_name} -> {home}-{away} (tot: {total})")
                return total >= 1
    print(f"[TRADING] TheSportsDB: nessun risultato per {match_name}")
    return None

def execute_entry(match, campionato, volume, quota, event_id="", whale_max=0, whale_tot=0):
    existing = get_giocata_by_match(match, "IN_CORSO")
    if existing:
        print(f"[TRADING] SKIP {match}: gia in corso (#{existing['id']})")
        return None
    giocata_id = inserisci_giocata(match, campionato, volume, quota, event_id)
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

def resolve_match(giocata):
    quota_entry = giocata["quota_reale"]
    event_id = giocata.get("event_id", "")
    match = giocata["match"]
    is_win = None
    smarkets_result = None
    sportsdb_result = None
    
    if event_id:
        smarkets_result = check_over_05_result(event_id)
    sportsdb_result = check_sportsdb(match)
    
    if smarkets_result is not None and sportsdb_result is not None:
        if smarkets_result == sportsdb_result:
            is_win = smarkets_result
            print(f"[TRADING] Doppia conferma: Smarkets={smarkets_result} TheSportsDB={sportsdb_result}")
        else:
            print(f"[TRADING] DISCREPANZA: Smarkets={smarkets_result} TheSportsDB={sportsdb_result}")
            return {"discrepancy": True, "smarkets": smarkets_result, "sportsdb": sportsdb_result, "match": match, "id": giocata["id"]}
    elif smarkets_result is not None:
        is_win = smarkets_result
        print(f"[TRADING] Solo Smarkets: {match} -> {'GOAL' if is_win else '0-0'}")
    elif sportsdb_result is not None:
        is_win = sportsdb_result
        print(f"[TRADING] Solo TheSportsDB: {match} -> {'GOAL' if is_win else '0-0'}")
    else:
        print(f"[TRADING] Nessuna fonte disponibile per {match}, riprovo al prossimo scan")
        return None
    
    if is_win:
        gross_profit = STAKE * (quota_entry - 1)
        net_profit = gross_profit * (1 - COMMISSION_RATE)
        esito = "VINTA"
    else:
        net_profit = -STAKE
        esito = "PERSA"
    aggiorna_esito(giocata["id"], esito, net_profit)
    print(f"[TRADING] GIOCATA #{giocata['id']}: {esito} | Profitto netto: {net_profit:.2f}€")
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
