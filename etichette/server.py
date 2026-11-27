#!/usr/bin/env python3
"""Server locale per il generatore di etichette.

Serve i file di questa cartella e inoltra le richieste /api/... all'API Mindat
(https://api.mindat.org/v1/...) aggiungendo la chiave. Così la chiave non
finisce nel browser e si evitano i problemi CORS.

Chiave: variabile d'ambiente MINDAT_API_KEY, oppure file `.mindat_key`
in questa cartella (è nel .gitignore, non viene committato).

Uso:
    python3 server.py            # poi apri http://localhost:8765
    python3 server.py 9000       # porta diversa
"""
import http.server
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.mindat.org/v1/"


def load_key():
    key = os.environ.get("MINDAT_API_KEY", "").strip()
    if not key:
        path = os.path.join(HERE, ".mindat_key")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                key = f.read().strip()
    return key


KEY = load_key()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def do_GET(self):
        if self.path == "/api/__ping":
            return self.send_json(200, {"proxy": True, "key": bool(KEY)})
        if self.path.startswith("/api/"):
            return self.proxy(self.path[len("/api/"):])
        return super().do_GET()

    def proxy(self, rest):
        if not KEY:
            return self.send_json(500, {"detail": "Chiave Mindat mancante: imposta MINDAT_API_KEY o crea .mindat_key"})
        req = urllib.request.Request(API + rest, headers={
            "Authorization": "Token " + KEY,
            "Accept": "application/json",
            "User-Agent": "mineral-label-generator/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body, status = r.read(), r.status
        except urllib.error.HTTPError as e:
            body, status = e.read(), e.code
        except Exception as e:  # rete, timeout...
            return self.send_json(502, {"detail": str(e)})
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, obj):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    if not KEY:
        print("ATTENZIONE: nessuna chiave Mindat (MINDAT_API_KEY o .mindat_key)")
    print(f"Generatore etichette su http://localhost:{port}")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
