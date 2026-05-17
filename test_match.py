from data_source import scan_markets
matches = scan_markets()
if matches:
    matches.sort(key=lambda x: x["volume"], reverse=True)
    for m in matches:
        print(f"MATCH: [{m['match']}] CAMP: [{m['campionato']}] VOL: {m['volume']:.0f} QUOTA: {m['quota']}")
else:
    print("Nessun match con i criteri attuali (volume >= 15000, quota 1.03-1.10)")
