from betfair_data import _headers, _api_call
import json

# Get catalogue
catalogue = _api_call("listMarketCatalogue/", {
    "filter": {"eventTypeIds": ["1"], "inPlayOnly": True},
    "marketProjection": ["EVENT", "RUNNER_DESCRIPTION", "COMPETITION"],
    "maxResults": 100
})

if catalogue:
    ou05 = [m for m in catalogue if "Over/Under 0.5 Goals" in m.get("marketName", "")]
    print(f"Over/Under 0.5 markets: {len(ou05)}")
    for m in ou05:
        print(f"  Market: {m.get('marketName')}")
        print(f"  Event: {m.get('event', {}).get('name')}")
        print(f"  Market ID: {m.get('marketId')}")
        
        # Get book
        book = _api_call("listMarketBook/", {
            "marketIds": [m["marketId"]],
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS", "EX_ALL_OFFERS"],
                "side": "BACK"
            }
        })
        
        if book and isinstance(book, list):
            b = book[0]
            print(f"  Status: {b.get('status')}")
            print(f"  Total matched: {b.get('totalMatched')}")
            print(f"  Total available: {b.get('totalAvailable')}")
            print(f"  Runners: {len(b.get('runners', []))}")
            for r in b.get("runners", []):
                ex = r.get("ex", {})
                back = ex.get("availableToBack", [])
                print(f"    Runner {r.get('selectionId')}: back_prices={len(back)}")
                if back:
                    for p in back[:3]:
                        print(f"      price={p.get('price')} size={p.get('size')}")
