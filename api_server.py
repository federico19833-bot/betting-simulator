from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
import os
import threading
from config import DB_PATH, STAKE, COMMISSION_RATE, INITIAL_BALANCE

DB = DB_PATH
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def do_correct(body):
    gid = body.get('id')
    esito = body.get('esito')
    risultato = body.get('risultato', '')
    if not gid or esito not in ('VINTA', 'PERSA', 'IN_CORSO'):
        return {'error': 'Parametri non validi'}, 400
    conn = get_db()
    row = conn.execute("SELECT * FROM giocate WHERE id=?", (gid,)).fetchone()
    if not row:
        conn.close()
        return {'error': 'Giocata non trovata'}, 404
    row = dict(row)
    quota = row['quota_reale']
    if esito == 'VINTA':
        net = STAKE * (quota - 1) * (1 - COMMISSION_RATE)
    elif esito == 'PERSA':
        net = -STAKE
    else:
        net = 0.0
    conn.execute("UPDATE giocate SET esito=?, profitto_netto=?, risultato=? WHERE id=?", (esito, round(net, 2), risultato, gid))
    conn.commit()
    conn.close()
    print(f"[API] Correzione #{gid}: {esito} {risultato} profitto={net:.2f}")
    return {'ok': True, 'id': gid, 'esito': esito, 'profitto': round(net, 2)}, 200

def do_delete(body):
    gid = body.get('id')
    if not gid:
        return {'error': 'ID mancante'}, 400
    conn = get_db()
    conn.execute("DELETE FROM giocate WHERE id=?", (gid,))
    conn.commit()
    conn.close()
    print(f"[API] Eliminata giocata #{gid}")
    return {'ok': True, 'id': gid}, 200

def deploy_dashboard():
    try:
        from generate_dashboard import generate
        generate(deploy=True)
    except Exception as e:
        print(f"[API] Errore deploy: {e}")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        if path.startswith('/api/giocate'):
            conn = get_db()
            rows = conn.execute("SELECT * FROM giocate ORDER BY id DESC").fetchall()
            conn.close()
            data = [dict(r) for r in rows]
            self._send_json(data)
        elif path == '/' or path == '/index.html':
            self._serve_file('correct.html')
        elif path == '/data.json':
            self._serve_file('data.json')
        elif path == '/correct.html':
            self._serve_file('correct.html')
        else:
            filename = path.lstrip('/')
            filepath = os.path.join(DOCS_DIR, filename)
            if os.path.isfile(filepath):
                self._serve_file(filename)
            else:
                self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
        if self.path.startswith('/api/correct'):
            result, status = do_correct(body)
            self._send_json(result, status)
            threading.Thread(target=deploy_dashboard, daemon=True).start()
        elif self.path.startswith('/api/delete'):
            result, status = do_delete(body)
            self._send_json(result, status)
            threading.Thread(target=deploy_dashboard, daemon=True).start()
        else:
            self.send_error(404)

    def _serve_file(self, filename):
        filepath = os.path.join(DOCS_DIR, filename)
        if not os.path.isfile(filepath):
            self.send_error(404)
            return
        ext = os.path.splitext(filename)[1]
        content_type = MIME_TYPES.get(ext, 'application/octet-stream')
        with open(filepath, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass

def run(port=5555):
    server = HTTPServer(('127.0.0.1', port), Handler)
    print(f"[API] Dashboard + API su http://localhost:{port}")
    server.serve_forever()

if __name__ == '__main__':
    run()