from data_source import scan_markets
from betfair_data import scan_over05_inplay
import json

print("=== SCANNING ===")
results = scan_markets()
print(f"\nSegnali di entrata: {len(results)}")
for r in results:
    print(f"  ENTRY: {r['match']} | {r['quota']} | {r['volume']:.0f}EUR | {r['source']}")

tracked = json.load(open("tracked_matches.json", "r", encoding="utf-8"))
print(f"\nTracked: {len(tracked)}")
for k, v in tracked.items():
    entered = "ENTRATA" if v.get("entered") else "watch"
    print(f"  {v['match']:40s} quota={v['last_price']} best_vol={v.get('best_volume',0):.0f} [{entered}]")