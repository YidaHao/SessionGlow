"""Bounded loopback receiver. The GUI drains the queue on its own thread."""

import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port=8790):
        self.events = queue.Queue(128)
        self.snapshot = {"app": "SessionGlow", "sessions": [], "connections": 0}
        self.thread = None
        super().__init__(("127.0.0.1", port), Handler)
        self.port = self.server_address[1]

    def get_request(self):
        sock, addr = super().get_request()
        sock.settimeout(2)
        return sock, addr

    def start(self):
        self.thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        if self.thread:
            self.shutdown()
            self.thread.join(timeout=3)
        self.server_close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path != "/health":
            self.send_error(404)
            return
        body = json.dumps(self.server.snapshot, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/opencode":
            self.send_error(404)
            return
        if self.headers.get("Origin") or self.headers.get("Transfer-Encoding"):
            self.send_error(403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 512 * 1024:
                self.send_error(413)
                return
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError()
            body = json.loads(raw)
            if not isinstance(body, dict):
                raise ValueError()
        except (OSError, ValueError, UnicodeError):
            self.send_error(400)
            return
        try:
            self.server.events.put_nowait(body)
        except queue.Full:
            self.send_error(503)
            return
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()
