from trading import check_sportsdb

matches = [
    "Jaguares de Cordoba v Independiente Yumbo",
    "Union Magdalena v Bogota",
]

for m in matches:
    result = check_sportsdb(m)
    print(f"{m}: {'GOAL' if result else '0-0' if result is not None else 'N/A'} (result={result})")