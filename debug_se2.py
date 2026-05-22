from selenium_query import _get_driver
from selenium.webdriver.common.by import By
import time

driver = _get_driver()
driver.get('https://www.betfair.it/exchange/plus/football/market/1.258392342')
time.sleep(5)

# Get Over 0.5 runner row HTML
runners = driver.find_elements(By.CSS_SELECTOR, 'h3.runner-name')
for r in runners:
    if 'Over' in r.text and '0' in r.text:
        over_runner = r
        break

row = over_runner.find_element(By.XPATH, './ancestor::tr')
row_html = row.get_attribute('innerHTML')

# Save to file
with open(r'C:\Users\feder\Desktop\betting-simulator\debug_row.html', 'w', encoding='utf-8') as f:
    f.write(row_html)
print(f'Row HTML saved ({len(row_html)} chars)')

# Try JavaScript to get Angular data
try:
    result = driver.execute_script("""
        var runners = document.querySelectorAll('h3.runner-name');
        for (var i = 0; i < runners.length; i++) {
            if (runners[i].textContent.indexOf('Over 0') >= 0) {
                var row = runners[i].closest('tr');
                if (!row) row = runners[i].parentElement;
                // Get all text content
                var cells = row.querySelectorAll('td');
                var texts = [];
                for (var j = 0; j < cells.length; j++) {
                    texts.push(cells[j].textContent.trim().substring(0, 50));
                }
                return texts.join(' | ');
            }
        }
        return 'NOT FOUND';
    """)
    print(f'\nJS cell texts: {result}')
except Exception as e:
    print(f'JS error: {e}')

# Try getting price via ng-binding or Angular attributes  
try:
    result = driver.execute_script("""
        var runners = document.querySelectorAll('h3.runner-name');
        for (var i = 0; i < runners.length; i++) {
            if (runners[i].textContent.indexOf('Over 0') >= 0) {
                var row = runners[i].closest('tr');
                // Get all back buttons
                var backs = row.querySelectorAll('button.back, [class*="back"]');
                var prices = [];
                for (var j = 0; j < backs.length; j++) {
                    var labels = backs[j].querySelectorAll('label');
                    var texts = [];
                    for (var k = 0; k < labels.length; k++) {
                        if (labels[k].textContent.trim()) texts.push(labels[k].textContent.trim());
                    }
                    prices.push({
                        class: backs[j].className.substring(0, 60),
                        title: backs[j].getAttribute('title'),
                        best: backs[j].getAttribute('is-best-selection'),
                        labels: texts
                    });
                }
                return JSON.stringify(prices);
            }
        }
        return 'NOT FOUND';
    """)
    print(f'\nJS back buttons: {result}')
except Exception as e:
    print(f'JS error: {e}')

# Try: get innerText of the entire row
try:
    result = driver.execute_script("""
        var runners = document.querySelectorAll('h3.runner-name');
        for (var i = 0; i < runners.length; i++) {
            if (runners[i].textContent.indexOf('Over 0') >= 0) {
                return runners[i].closest('tr').innerText;
            }
        }
        return 'NOT FOUND';
    """)
    print(f'\nRow innerText:\n{result}')
except Exception as e:
    print(f'JS error: {e}')

from selenium_query import close
close()