from betfair_data import scan_over05_inplay
import json

results = scan_over05_inplay()
print(f"Betfair results: {len(results)}")
for r in results:
    print(f"  {r['match']}: quota={r['quota']} vol={r['volume']} src={r['source']}")
