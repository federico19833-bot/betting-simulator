from selenium_query import _get_driver
from selenium.webdriver.common.by import By
import time

driver = _get_driver()
driver.get('https://www.betfair.it/exchange/plus/football/market/1.258392342')
time.sleep(5)

runners = driver.find_elements(By.CSS_SELECTOR, 'h3.runner-name')
over_runner = None
for r in runners:
    if 'Over' in r.text and '0' in r.text:
        over_runner = r
        print(f'Found: {r.text}')
        break

if over_runner:
    row = over_runner.find_element(By.XPATH, './ancestor::tr')
    
    # All buttons
    btns = row.find_elements(By.CSS_SELECTOR, 'button')
    print(f'Buttons: {len(btns)}')
    for b in btns[:15]:
        cls = b.get_attribute('class') or ''
        title = b.get_attribute('title') or ''
        best = b.get_attribute('is-best-selection') or ''
        labels = b.find_elements(By.CSS_SELECTOR, 'label')
        lbl_text = [l.text for l in labels]
        print(f'  class={cls[:80]} title={title} best={best} labels={lbl_text}')

    # All labels directly 
    labels = row.find_elements(By.CSS_SELECTOR, 'label')
    print(f'\nLabels: {len(labels)}')
    for l in labels[:20]:
        txt = l.text.strip()
        cls = l.get_attribute('class') or ''
        print(f'  label class={cls[:60]} text=[{txt}]')

    # Check for suspended status
    suspended = row.find_elements(By.CSS_SELECTOR, '.suspended')
    print(f'\nSuspended elements: {len(suspended)}')

from selenium_query import close
close()