"""
helpers/healthcheck.py — Render.com "Web Service" type ko ek open $PORT
chahiye hota hai health-check ke liye. Ye bot hai, website nahi — isliye
sirf ek chhota background HTTP server chala dete hain jo "/" pe "OK"
return karta hai. Koi extra dependency (Flask/gunicorn) nahi lagti.
"""

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Video Download Bot is running.")

    def log_message(self, format, *args):
        pass  # chup rehna — bot ke logs ke saath mix nahi hone dena


def start_healthcheck_server(port: int):
    def _serve():
        server = HTTPServer(("0.0.0.0", port), _Handler)
        server.serve_forever()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
