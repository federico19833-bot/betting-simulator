import json
tracked = json.load(open('tracked_matches.json', 'r', encoding='utf-8'))
for k, v in tracked.items():
    if 'Jaguares' in v.get('match', '') or 'Union Magdalena' in v.get('match', ''):
        vol = v.get('volume', '?')
        best = v.get('best_volume', '?')
        print(f"{k}: {v['match']} | volume={vol} | best_volume={best}")