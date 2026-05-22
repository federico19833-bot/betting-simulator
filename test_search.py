import requests

THESPORTSDB = "https://www.thesportsdb.com/api/v1/json/3"

tests = [
    "Ajax_v_FC_Groningen",
    "Ajax_vs_FC_Groningen",
    "Anderlecht_v_Sint_Truiden",
    "Anderlecht_vs_Sint_Truiden",
    "Wolfsburg_v_Paderborn",
    "Brondby_v_FC_Copenhagen",
    "Al_Najma_BRN_v_Al_Ittihad_BRN",
    "Al-Kholood_Club_v_Al-Fateh_KSA",
    "BFC_Daugavpils_v_Ogre_United",
]

for t in tests:
    r = requests.get(f"{THESPORTSDB}/searchevents.php?e={t}", timeout=10)
    d = r.json()
    events = d.get("event") or []
    if events:
        for ev in events[:2]:
            home = ev.get("strHomeTeam","")
            away = ev.get("strAwayTeam","")
            hs = ev.get("intHomeScore","")
            aws = ev.get("intAwayScore","")
            print(f"  {t}: {home} {hs}-{aws} {away}")
    else:
        print(f"  {t}: NON TROVATO")