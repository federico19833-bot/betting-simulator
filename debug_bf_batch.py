from betfair_data import _headers, _api_call
import json

headers = _headers()

# Check what markets are found first
catalogue = _api_call("listMarketCatalogue/", {
    "filter": {"eventTypeIds": ["1"], "inPlayOnly": True},
    "marketProjection": ["EVENT", "RUNNER_DESCRIPTION", "COMPETITION"],
    "maxResults": 200
})

ou05 = []
for m in catalogue:
    if "Over/Under 0.5 Goals" in m.get("marketName", ""):
        ou05.append(m)

print(f"Found {len(ou05)} Over/Under 0.5 markets:")
for m in ou05:
    print(f"  {m.get('event', {}).get('name')} | Market ID: {m.get('marketId')}")
    for r in m.get("runners", []):
        print(f"    {r.get('runnerName')} (ID: {r.get('selectionId')})")

# Now call market book for all of them together
market_ids = [m["marketId"] for m in ou05]
print(f"\nCalling listMarketBook for: {market_ids}")

book = _api_call("listMarketBook/", {
    "marketIds": market_ids,
    "priceProjection": {"priceData": ["EX_BEST_OFFERS"], "side": "BACK"}
})

if book:
    for j, b in enumerate(book):
        mid = b.get("marketId")
        status = b.get("status")
        matched = b.get("totalMatched")
        over_price = 0
        over_vol = 0
        for r in b.get("runners", []):
            sid = r.get("selectionId")
            back = r.get("ex", {}).get("availableToBack", [])
            # Find Over 0.5 runner (selectionId 5851483)
            if sid == 5851483 and back:
                over_price = back[0]["price"]
                over_vol = sum(p["size"] for p in back)
            elif sid == 5851482 and back:
                under_info = f"({back[0]['price']})"
        
        name = ou05[j]["event"]["name"] if j < len(ou05) else "?"
        print(f"  [{j}] {name} | status={status} | Over={over_price} vol={over_vol}")
