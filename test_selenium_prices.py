from selenium_query import get_realtime_over05
import time

markets = [
    ("1.258325413", "Ajax v FC Groningen"),
    ("1.258342006", "Jamshedpur FC v Odisha"),
    ("1.258447234", "Qatar v Sudan"),
]

for mid, name in markets:
    print(f"\n--- {name} (market {mid}) ---")
    price = get_realtime_over05(mid)
    print(f"Result: {price}")
    time.sleep(2)

from selenium_query import close
close()