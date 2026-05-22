import re

with open(r"C:\Users\feder\Desktop\betting-simulator\debug_betfair.html", "r", encoding="utf-8") as f:
    html = f.read()

idx = html.find("Over 0,5 goal")
if idx > 0:
    chunk = html[idx:idx+3000]
    
    # Look for the structure around Over 0.5
    # Find selections with id 5851483 (Over 0.5)
    sel_idx = chunk.find("5851483")
    if sel_idx > 0:
        sel_chunk = chunk[sel_idx:sel_idx+1500]
        print("=== Selection 5851483 (Over 0.5) ===")
        print(sel_chunk[:1500])
    
    # Find all back-cell sections  
    print("\n=== Back cells ===")
    backs = [m.start() for m in re.finditer(r"back-cell", chunk)]
    print(f"Found {len(backs)} back cells")
    for pos in backs[:5]:
        print(chunk[pos:pos+300])
        print("---")
    
    # Find label values near Over 0.5
    print("\n=== Labels in Over 0.5 area ===")
    labels = re.findall(r'<label[^>]*class="([^"]*)"[^>]*>([^<]+)</label>', chunk)
    for cls, val in labels[:10]:
        print(f"  class='{cls}' value='{val}'")