import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

try:
    url = "https://www.betfair.it/exchange/football/market?id=1.258325413"
    print(f"Loading: {url}")
    driver.get(url)
    time.sleep(5)
    
    print(f"Title: {driver.title}")
    print(f"URL: {driver.current_url}")
    
    page_src = driver.page_source
    print(f"Page length: {len(page_src)}")
    
    with open(r"C:\Users\feder\Desktop\betting-simulator\debug_betfair.html", "w", encoding="utf-8") as f:
        f.write(page_src)
    print("Saved page source to debug_betfair.html")
    
    try:
        runners = driver.find_elements(By.CSS_SELECTOR, ".runner-index, .runner-name, [data-runner-id]")
        print(f"Found {len(runners)} runner elements")
        for r in runners[:10]:
            print(f"  Runner: {r.text[:100]}")
    except Exception as e:
        print(f"Runner search error: {e}")
    
    try:
        prices = driver.find_elements(By.CSS_SELECTOR, ".bet-button, .price, [data-price]")
        print(f"Found {len(prices)} price elements")
        for p in prices[:10]:
            print(f"  Price: {p.text[:50]}")
    except Exception as e:
        print(f"Price search error: {e}")
    
    try:
        odds_cells = driver.find_elements(By.CSS_SELECTOR, "td, .mv-runner-container, .marketview-runner-container")
        print(f"Found {len(odds_cells)} odds cells")
        for o in odds_cells[:5]:
            print(f"  Cell: {o.text[:100]}")
    except Exception as e:
        print(f"Odds cell error: {e}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()