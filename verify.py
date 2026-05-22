import time, json, os

os.chdir(r"C:\Users\feder\Desktop\betting-simulator")
time.sleep(35)

try:
    with open("last_scan.json", "r") as f:
        data = json.load(f)
    print(f"Eventi trovati: {len(data)}")
    for e in data:
        src = e.get("source", "?")
        match = e.get("match", "?")
        quota = e.get("quota", 0)
        vol = e.get("volume", 0)
        print(f"  {src}: {match} | quota={quota} | vol={vol}")
except Exception as ex:
    print(f"Errore last_scan: {ex}")

try:
    with open("tracked_matches.json", "r") as f:
        tracked = json.load(f)
    print(f"Match monitorati: {len(tracked)}")
    for k, v in tracked.items():
        match = v.get("match", "?")
        price = v.get("last_price", 0)
        vol = v.get("volume", 0)
        entered = v.get("entered", False)
        print(f"  {k}: {match} | price={price} | vol={vol} | entered={entered}")
except Exception as ex:
    print(f"Errore tracked: {ex}")
