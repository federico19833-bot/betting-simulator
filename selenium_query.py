import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

_driver = None
_driver_last_used = 0

def _get_driver():
    global _driver, _driver_last_used
    if _driver and time.time() - _driver_last_used < 300:
        _driver_last_used = time.time()
        return _driver
    _close_driver()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=it")
    prefs = {"profile.default_content_setting_values.notifications": 2}
    options.add_experimental_option("prefs", prefs)
    _driver = webdriver.Chrome(options=options)
    _driver.set_page_load_timeout(20)
    _driver_last_used = time.time()
    return _driver

def _close_driver():
    global _driver
    if _driver:
        try:
            _driver.quit()
        except:
            pass
        _driver = None

def get_realtime_over05(market_id):
    driver = _get_driver()
    url = f"https://www.betfair.it/exchange/plus/football/market/{market_id}"
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h3.runner-name, .runner-name"))
        )
        time.sleep(3)
        
        runners = driver.find_elements(By.CSS_SELECTOR, "h3.runner-name")
        over_runner = None
        for r in runners:
            name = r.text.strip()
            if "Over" in name and ("0,5" in name or "0.5" in name):
                over_runner = r
                break
        
        if not over_runner:
            print(f"[SELENIUM] Runner Over 0.5 non trovato per market {market_id}")
            all_runners = driver.find_elements(By.CSS_SELECTOR, "h3")
            for r in all_runners:
                print(f"  Runner: '{r.text.strip()}'")
            return None
        
        runner_name = over_runner.text.strip()
        row = over_runner.find_element(By.XPATH, "./ancestor::tr")
        if not row:
            print(f"[SELENIUM] Nessuna riga per {runner_name}")
            return None
        
        row_text = row.text
        is_suspended = "sospeso" in row_text.lower() or "suspended" in row_text.lower()
        if is_suspended:
            print(f"[SELENIUM] {runner_name}: mercato SOSPESO (gol?)")
            return -1
        
        cell_text = driver.execute_script("""
            var runners = document.querySelectorAll('h3.runner-name');
            for (var i = 0; i < runners.length; i++) {
                if (runners[i].textContent.indexOf('Over 0') >= 0) {
                    var row = runners[i].closest('tr');
                    return row.innerText;
                }
            }
            return '';
        """)
        
        if not cell_text:
            print(f"[SELENIUM] Nessun testo per {runner_name}")
            return None
        
        import re
        prices = re.findall(r'(\d+[,.]\d{2,3})', cell_text)
        back_prices = []
        for p_str in prices:
            try:
                val = float(p_str.replace(",", "."))
                if 1.01 <= val <= 50.0:
                    back_prices.append(val)
            except:
                pass
        
        if not back_prices:
            print(f"[SELENIUM] {runner_name}: nessun prezzo visibile (probabile pre-match senza back)")
            return "NO_BACK_PRICES"
        
        best_back = max(back_prices)
        print(f"[SELENIUM] {runner_name}: best back = {best_back} (all: {back_prices})")
        return best_back
        
    except Exception as e:
        print(f"[SELENIUM] Errore market {market_id}: {e}")
        _close_driver()
        return None
        
        runner_name = over_runner.text.strip()
        row = over_runner.find_element(By.XPATH, "./ancestor::tr")
        if not row:
            print(f"[SELENIUM] No row for {runner_name}")
            return None
        
        back_cells = row.find_elements(By.CSS_SELECTOR, "td.back-cell")
        if not back_cells:
            buttons = row.find_elements(By.CSS_SELECTOR, "button.back")
        else:
            buttons = []
            for cell in back_cells:
                cell_btns = cell.find_elements(By.CSS_SELECTOR, "button")
                buttons.extend(cell_btns)
        
        back_prices = []
        for btn in buttons:
            btn_class = btn.get_attribute("class") or ""
            if "back" not in btn_class.lower():
                continue
            is_best = btn.get_attribute("is-best-selection") or ""
            title = btn.get_attribute("title") or ""
            labels = btn.find_elements(By.CSS_SELECTOR, "label")
            for lbl in labels:
                txt = lbl.text.strip().replace(",", ".")
                try:
                    val = float(txt)
                    if 1.01 <= val <= 50.0:
                        is_best_flag = is_best == "true"
                        back_prices.append((val, is_best_flag, lbl.get_attribute("class") or ""))
                except:
                    pass
        
        if back_prices:
            best_back = max(p[0] for p in back_prices)
            best_flagged = [p[0] for p in back_prices if p[1]]
            if best_flagged:
                chosen = best_flagged[0]
            else:
                chosen = best_back
            print(f"[SELENIUM] {runner_name}: best back = {chosen} (all backs: {[p[0] for p in back_prices]})")
            return chosen
        
        back_btns = row.find_elements(By.CSS_SELECTOR, "button[class*='back']")
        for btn in back_btns:
            lbl = btn.find_element(By.CSS_SELECTOR, "label")
            txt = lbl.text.strip().replace(",", ".")
            try:
                val = float(txt)
                if 1.01 <= val <= 50.0:
                    print(f"[SELENIUM] {runner_name}: back price = {val} (button fallback)")
                    return val
            except:
                pass
        
        print(f"[SELENIUM] Nessun prezzo back trovato per {runner_name}")
        return None
        
    except Exception as e:
        print(f"[SELENIUM] Errore market {market_id}: {e}")
        _close_driver()
        return None

def close():
    _close_driver()