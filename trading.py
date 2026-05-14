from config import STAKE, COMMISSION_RATE
from database import inserisci_giocata, aggiorna_esito, get_giocate_in_corso, get_giocata_by_match
import time

SIMULATED_DELAY_MINUTES = 90

def get_contracts(market_id):
    import requests
    try:
        r = requests.get(f"https://api.smarkets.com/v3/markets/{market_id}/contracts/", timeout=10)
        return r.json().get("contracts", []) if r.status_code == 200 else []
    except:
        return []

def execute_entry(match, campionato, volume, quota, event_id=""):
    existing = get_giocata_by_match(match, "IN_CORSO")
    if existing:
        print(f"[TRADING] SKIP {match}: gia in corso (#{existing['id']})")
        return None
    giocata_id = inserisci_giocata(match, campionato, volume, quota, event_id)
    print(f"[TRADING] GIOCATA ENTRATA #{giocata_id}: {match} | Quota {quota} | Stake {STAKE}€")
    return giocata_id

def check_over_05_result(event_id):
    import requests
    try:
        r = requests.get(f"https://api.smarkets.com/v3/events/{event_id}/markets/", timeout=10)
        if r.status_code != 200:
            return None
        markets = r.json().get("markets", [])
        for m in markets:
            mt = m.get("market_type", {})
            if isinstance(mt, dict) and mt.get("name") == "OVER_UNDER" and mt.get("param") == "0.5":
                mid = m.get("id")
                contracts = get_contracts(mid)
                for c in contracts:
                    ct = c.get("contract_type", {})
                    if isinstance(ct, dict) and ct.get("name") == "OVER":
                        state = c.get("state_or_outcome", "")
                        if state == "won":
                            return True
                        elif state == "lost":
                            return False
                        return None
        return None
    except:
        return None

def resolve_match(giocata):
    quota_entry = giocata["quota_reale"]
    event_id = giocata.get("event_id", "")
    is_win = None
    if event_id:
        is_win = check_over_05_result(event_id)
    if is_win is None:
        print(f"[TRADING] Nessun risultato reale per {giocata['match']}, random 65%")
        import random
        is_win = random.random() < 0.65
    if is_win:
        gross_profit = STAKE * (quota_entry - 1)
        net_profit = gross_profit * (1 - COMMISSION_RATE)
        esito = "VINTA"
    else:
        net_profit = -STAKE
        esito = "PERSA"
    aggiorna_esito(giocata["id"], esito, net_profit)
    print(f"[TRADING] GIOCATA #{giocata['id']}: {esito} | Profitto netto: {net_profit:.2f}€")
    return is_win, net_profit

def check_and_resolve_pending():
    in_corso = get_giocate_in_corso()
    for g in in_corso:
        from datetime import datetime
        orario = datetime.fromisoformat(g["orario"])
        elapsed = (datetime.now() - orario).total_seconds() / 60
        if elapsed >= SIMULATED_DELAY_MINUTES:
            resolve_match(g)
