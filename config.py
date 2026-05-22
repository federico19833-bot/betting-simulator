import os

TELEGRAM_TOKEN = "8951372656:AAEqgCmA4nWQFr1dh5fBPmOsyEohn9uVY7A"
TELEGRAM_CHAT_ID = "480114363"

STAKE = 100.0
COMMISSION_RATE = 0.05
MIN_ODDS = 1.08
MAX_ODDS = 1.10
VOLUME_THRESHOLD = 8000
INITIAL_BALANCE = 1000.0
BETFAIR_APP_KEY = "69ELmrb2twFe9hus"
BETFAIR_USERNAME = "federico1983@hotmail.it"
BETFAIR_PASSWORD = "Fedeele86."

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "simulazione_betting.db")
EQUITY_CHART_PATH = "reports/andamento_strategia.png"
POLL_INTERVAL_SECONDS = 30
