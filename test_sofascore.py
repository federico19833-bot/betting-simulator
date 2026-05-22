import requests, re

r = requests.get('https://www.sofascore.com/football', headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
})
print(f"Status: {r.status_code}, Length: {len(r.text)}")
urls = re.findall(r'(https?://[^\s"\'<>]+api[^\s"\'<>]*)', r.text)
print(f"API URLs: {len(urls)}")
for u in urls[:5]:
    print(u)

# Try Sofascore with a session (mimic browser)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.sofascore.com',
    'Referer': 'https://www.sofascore.com/',
})

# First visit the homepage to get cookies
session.get('https://www.sofascore.com/')

# Then try the API
r2 = session.get('https://api.sofascore.com/api/v1/search/football?q=Ajax')
print(f"\nAPI Status: {r2.status_code}")
print(f"API Response: {r2.text[:500]}")