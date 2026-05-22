import sqlite3
from trading import check_sportsdb, check_betfair_result

match = "Slavia Sofia v Montana"
result = check_sportsdb(match)
print(f"TheSportsDB: {result}")

result_bf = check_betfair_result("1.258377970")
print(f"Betfair: {result_bf}")