from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.models import SourceConfig


CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "/app/sandbox/candidates/good.json"))
CONFIG = SourceConfig.model_validate_json(CONFIG_PATH.read_bytes())


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": CONFIG.service_id})
        elif self.path == "/ready":
            if CONFIG.maintenance_mode:
                self._send(503, {"status": "maintenance"})
            else:
                self._send(200, {"status": "ready"})
        elif self.path == "/config":
            self._send(200, CONFIG.model_dump())
        else:
            self._send(404, {"status": "not_found"})

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
