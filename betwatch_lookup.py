"""
Uso: python betwatch_lookup.py <URL_BETWATCH>
Esempio: python betwatch_lookup.py https://betwatch.fr/football/35568174

Scarica i dati reali Betfair da Betwatch e verifica la strategia.
"""

import sys
import cloudscraper
import re
from config import VOLUME_THRESHOLD, MIN_ODDS, MAX_ODDS

if len(sys.argv) < 2:
    url = input("Incolla URL Betwatch: ").strip()
else:
    url = sys.argv[1]

if "betwatch.fr" not in url:
    print("URL non valido. Deve essere https://betwatch.fr/football/...")
    sys.exit(1)

scraper = cloudscraper.create_scraper()
r = scraper.get(url, timeout=20)

if r.status_code != 200:
    print(f"Errore: status {r.status_code}")
    sys.exit(1)

html = r.text

match_name = re.search(r"<title>(.+?)</title>", html, re.DOTALL)
match_name = re.sub(r"\s*\|\s*Betwatch.*", "", match_name.group(1)).strip() if match_name else "Sconosciuto"

# Trova Over 0.5 Goals nel JavaScript inline
m = re.search(r"game\s*=\s*({.*?});", html, re.DOTALL)
if not m:
    # Prova a cercare nel JSON API
    headers = {"X-Betwatch-Header": "XMLHttpRequest"}
    r2 = scraper.get(url, headers=headers, timeout=20)
    if r2.status_code == 200 and r2.text.startswith("{"):
        data = r2.json()
        for k, v in data.get("i", {}).items():
            name = v.get("name", "")
            if "0.5" in name:
                for rn in v.get("runners", []):
                    rname = rn.get("name", "").lower()
                    if rname == "over":
                        quota = float(rn.get("odd", 0) or 0)
                        volume = float(rn.get("volume", 0) or 0)
                        print(f"\n📊 {match_name}")
                        print(f"   Over 0.5: quota={quota} | volume={volume:,.0f}€")
                        if quota and volume:
                            print(f"\n--- STRATEGIA 1.05 ---")
                            if 1.03 <= quota <= 1.06:
                                print(f"   ✅ Quota {quota} in range OK")
                            else:
                                print(f"   ❌ Quota {quota} FUORI range 1.03-1.06")
                            if volume >= VOLUME_THRESHOLD:
                                print(f"   ✅ Volume {volume:,.0f}€ >= soglia {VOLUME_THRESHOLD:,.0f}€ OK")
                            else:
                                print(f"   ❌ Volume {volume:,.0f}€ < soglia {VOLUME_THRESHOLD:,.0f}€")
                            if 1.03 <= quota <= 1.06 and volume >= VOLUME_THRESHOLD:
                                print(f"\n🎯 SEGNALE VALIDO! Entra a 1.05 con 100€")
                                print(f"   VINTA: +4.75€ | PERSA: -100€")
                        break
        return

import ast
data = ast.literal_eval(m.group(1))
markets = data.get("i", {})

for k, v in markets.items():
    name = v.get("name", "")
    if "0.5" in name:
        runners = {r["name"].lower(): r for r in v.get("runners", [])}
        over = runners.get("over", {})
        under = runners.get("under", {})
        vol = float(over.get("volume", 0) or 0)
        quota = float(over.get("odd", 0) or 0)
        
        print(f"\n📊 {match_name}")
        print(f"   Link: {url}")
        print(f"   OVER 0.5: quota={quota} | volume={vol:,.0f}€")
        print(f"   UNDER 0.5: quota={under.get('odd','?')} | volume={float(under.get('volume',0) or 0):,.0f}€")
        
        if quota and vol:
            print(f"\n--- STRATEGIA 1.05 ---")
            print(f"   Range quote: 1.03-1.06 | Soglia volume: {VOLUME_THRESHOLD:,.0f}€")
            ok_quota = 1.03 <= quota <= 1.06
            ok_vol = vol >= VOLUME_THRESHOLD
            print(f"   {'✅' if ok_quota else '❌'} Quota {quota} {'in range' if ok_quota else 'FUORI range'}")
            print(f"   {'✅' if ok_vol else '❌'} Volume {vol:,.0f}€ {'>= ' + f'{VOLUME_THRESHOLD:,}€' if ok_vol else '< soglia'}")
            if ok_quota and ok_vol:
                print(f"\n🎯 SEGNALE VALIDO!")
                print(f"   Entra a 1.05 con 100€")
                print(f"   Se vince: +4.75€ netti")
                print(f"   Se perde: -100€")
            else:
                print(f"\n❌ SEGNALE NON VALIDO - aspetta quote/volume migliori")
        break
else:
    print("Mercato Over/Under 0.5 non trovato (match già iniziato o finito)")
