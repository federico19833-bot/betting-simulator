import json
import time
import threading
import websocket

SMARKETS_WS = "wss://api.smarkets.com/v3/ws"

class SmarketsWS:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.subscriptions = set()
        self.prev_books = {}
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self._reconnect_delay = 1
        self.last_whale = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()

    def subscribe(self, market_id, contract_id):
        with self.lock:
            if market_id not in self.subscriptions:
                self.subscriptions.add(market_id)
                if self.connected:
                    self._send_subscribe(market_id)

    def get_last_whale(self):
        with self.lock:
            return self.last_whale

    def clear_whale(self):
        with self.lock:
            self.last_whale = None

    def _run(self):
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(
                    SMARKETS_WS,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self.ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as e:
                print(f"[WS] Errore: {e}")
            if self.running:
                time.sleep(min(self._reconnect_delay, 30))
                self._reconnect_delay = min(self._reconnect_delay * 2, 30)

    def _on_open(self, ws):
        self.connected = True
        self._reconnect_delay = 1
        print(f"[WS] Connesso")
        with self.lock:
            for mid in self.subscriptions:
                self._send_subscribe(mid)

    def _on_close(self, ws, close_status=None, close_msg=None):
        self.connected = False
        print(f"[WS] Disconnesso ({close_status})")

    def _on_error(self, ws, error):
        pass

    def _send_subscribe(self, market_id):
        try:
            self.ws.send(json.dumps({
                "type": "subscribe",
                "channel": "quotes",
                "market_ids": [market_id]
            }))
        except:
            pass

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            if data.get("type") == "quotes":
                self._process_quotes(data)
        except:
            pass

    def _process_quotes(self, data):
        market_id = data.get("market_id")
        contract_quotes = data.get("contract_quotes", data.get("quotes", {}))
        if not contract_quotes or not market_id:
            return

        for contract_id, qdata in contract_quotes.items():
            bids = qdata.get("bids", [])
            key = (market_id, contract_id)

            with self.lock:
                prev_book = self.prev_books.get(key, {})
                new_book = {}

                for bid in bids:
                    price = float(bid.get("price", 0)) / 1000
                    qty = float(bid.get("quantity", 0)) / 100
                    if price > 0:
                        new_book[price] = qty

                # Detect individual whale orders
                for price, qty in new_book.items():
                    if 1.01 <= price <= 1.09:
                        prev_qty = prev_book.get(price, 0)
                        diff = qty - prev_qty
                        if diff >= 7000:
                            whale = {
                                "market_id": market_id,
                                "contract_id": contract_id,
                                "quota": round(price, 3),
                                "importo": round(diff),
                                "totale_livello": round(qty),
                                "timestamp": time.time()
                            }
                            self.last_whale = whale
                            print(f"[WS] BALENA {diff:.0f}€ a quota {price} su {market_id}")

                self.prev_books[key] = new_book


instances = {}

def get_ws():
    import os
    key = os.getpid()
    if key not in instances:
        ws = SmarketsWS()
        ws.start()
        time.sleep(2)
        instances[key] = ws
    return instances[key]
