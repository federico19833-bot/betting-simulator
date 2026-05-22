import requests

THESPORTSDB = "https://www.thesportsdb.com/api/v1/json/3"

teams = [
    ("Anderlecht", "Sint Truiden"),
    ("Wolfsburg", "Paderborn"),
    ("Brondby", "FC Copenhagen"),
    ("Panaitolikos", "Asteras Tripolis"),
    ("Al Najma", "Al Ittihad"),
    ("Al-Kholood", "Al-Fateh"),
    ("Al Nassr", "Dhamk"),
    ("Al-Hazm", "Al-Taawoun"),
    ("Jaguares de Cordoba", "Independiente Yumbo"),
    ("Deportes Recoleta", "Cobreloa"),
    ("Roma U20", "Bologna U20"),
]

for home, away in teams:
    r = requests.get(f"{THESPORTSDB}/searchevents.php?e={home}_vs_{away}", timeout=10)
    d = r.json()
    events = d.get("event") or []
    if events:
        for ev in events[:1]:
            h = ev.get("strHomeTeam","")
            a = ev.get("strAwayTeam","")
            hs = ev.get("intHomeScore","")
            aws = ev.get("intAwayScore","")
            print(f"  {home} vs {away}: {h} {hs}-{aws} {a}")
    else:
        # Try just home team
        r2 = requests.get(f"{THESPORTSDB}/searchevents.php?e={home.replace(' ', '_')}&s=2025-2026", timeout=10)
        d2 = r2.json()
        ev2 = d2.get("event") or []
        if ev2:
            print(f"  {home}: {len(ev2)} events found")
        else:
            r3 = requests.get(f"{THESPORTSDB}/searchteams.php?t={home.replace(' ', '_')}", timeout=10)
            d3 = r3.json()
            teams_data = d3.get("teams") or []
            if teams_data:
                tid = teams_data[0].get("idTeam","")
                r4 = requests.get(f"{THESPORTSDB}/eventslast.php?id={tid}", timeout=10)
                d4 = r4.json()
                results = d4.get("results") or []
                if results:
                    for ev in results[:2]:
                        print(f"    Last: {ev.get('strHomeTeam','')} {ev.get('intHomeScore','')}-{ev.get('intAwayScore','')} {ev.get('strAwayTeam','')}")
                else:
                    print(f"  {home}: team found ({teams_data[0].get('strTeam','')}) but no recent events")
            else:
                print(f"  {home}: NON TROVATO")