import cloudscraper, re, json, sys
sys.path.insert(0, "C:\\Users\\feder\\Desktop\\betting-simulator")

scraper = cloudscraper.create_scraper()
AJAX = {"X-Betwatch-Header": "XMLHttpRequest"}

# 1: Prova a trovare ID partite LIVE dalla homepage
html = scraper.get("https://betwatch.fr/", timeout=20).text

# Cerca pattern di event ID nel JavaScript
ids = set()
for m in re.finditer(r'(\d{5,})', html):
    ctx = html[max(0,m.start()-20):m.end()+20].lower()
    if "football" in ctx or "event" in ctx or "match" in ctx or "live" in ctx:
        ids.add(m.group(1))

print(f"Trovati {len(ids)} possibili ID")
ids_list = sorted(ids)[:20]
print(f"Campioni: {ids_list}")

# 2: Prova ogni ID per trovare Over 0.5 LIVE
for eid in ids_list[:10]:
    try:
        r = scraper.get(f"https://betwatch.fr/football/{eid}", headers=AJAX, timeout=10)
        if r.status_code != 200 or "i" not in r.text:
            continue
        data = r.json()
        for k, v in data.get("i", {}).items():
            name = v.get("name", "")
            if "0.5" in name:
                for rn in v.get("runners", []):
                    if rn.get("name", "").lower() == "over":
                        vol = float(rn.get("volume", 0) or 0)
                        odds = float(rn.get("odd", 0) or 0)
                        print(f"\nID {eid}: Over 0.5 quota={odds} volume={vol:,.0f}Euro")
    except:
        pass
