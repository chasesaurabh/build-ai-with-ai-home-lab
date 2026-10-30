from __future__ import annotations

import socket
import json
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator, Type

import pytest

from app.adapters import (
    AdapterResponseError,
    AdapterTimeoutError,
    AdapterUnavailableError,
    OpenAICompatibleAdapter,
)
from app.models import IntakeRequest


class QuietHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class InvalidEnvelopeHandler(QuietHandler):
    def do_POST(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"not-json")


class SlowHandler(QuietHandler):
    def do_POST(self) -> None:
        time.sleep(0.25)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")
        except (BrokenPipeError, ConnectionResetError):
            pass


class CaptureRequestHandler(QuietHandler):
    payload: dict[str, object] | None = None

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        type(self).payload = json.loads(self.rfile.read(length))
        content = {
            "category": "availability",
            "condition": "degraded",
            "affected_system": "media server",
            "evidence_requests": ["service_status", "recent_logs"],
            "rationale": "Intermittent service errors require a bounded human investigation.",
        }
        envelope = {
            "choices": [
                {
                    "message": {"content": json.dumps(content)},
                    "finish_reason": "stop",
                }
            ]
        }
        body = json.dumps(envelope).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@contextmanager
def temporary_server(handler: Type[BaseHTTPRequestHandler]) -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request() -> IntakeRequest:
    return IntakeRequest(
        description="The media server has returned intermittent errors during two recent requests."
    )


def test_invalid_provider_envelope_is_controlled_failure() -> None:
    with temporary_server(InvalidEnvelopeHandler) as base_url:
        adapter = OpenAICompatibleAdapter(base_url, "synthetic-model", timeout_seconds=1)
        with pytest.raises(AdapterResponseError, match="invalid response envelope"):
            adapter.classify(request())


def test_real_socket_timeout_is_controlled_failure() -> None:
    with temporary_server(SlowHandler) as base_url:
        adapter = OpenAICompatibleAdapter(base_url, "synthetic-model", timeout_seconds=0.05)
        with pytest.raises(AdapterTimeoutError, match="timed out"):
            adapter.classify(request())


def test_refused_connection_is_controlled_failure() -> None:
    reservation = socket.socket()
    reservation.bind(("127.0.0.1", 0))
    port = reservation.getsockname()[1]
    reservation.close()

    adapter = OpenAICompatibleAdapter(
        f"http://127.0.0.1:{port}",
        "synthetic-model",
        timeout_seconds=0.5,
    )
    with pytest.raises(AdapterUnavailableError, match="unavailable"):
        adapter.classify(request())


def test_structured_request_disables_model_thinking() -> None:
    CaptureRequestHandler.payload = None
    with temporary_server(CaptureRequestHandler) as base_url:
        adapter = OpenAICompatibleAdapter(base_url, "nemotron-35-lightning", timeout_seconds=1)
        adapter.classify(request())

    assert CaptureRequestHandler.payload is not None
    assert CaptureRequestHandler.payload["chat_template_kwargs"] == {"enable_thinking": False}


@pytest.mark.parametrize('body,status,expected', [
    (b'{"data":[{"id":"synthetic-model"}]}', 200, True),
    (b'{"data":[{"id":"synthetic-model-other"}]}', 200, False),
    (b'{"data":[]}', 200, False),
    (b'{"data":"synthetic-model"}', 200, False),
    (b'not-json', 200, False),
    (b'[]', 200, False),
    (b'{"data":[{"id":"synthetic-model"}]}', 401, False),
    (b' ' * 65_537, 200, False),
])
def test_readiness_requires_exact_model_in_bounded_listing(body, status, expected):
    paths = []
    class ListingHandler(QuietHandler):
        def do_GET(self):
            paths.append(self.path)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    with temporary_server(ListingHandler) as base_url:
        adapter = OpenAICompatibleAdapter(base_url, 'synthetic-model', timeout_seconds=1)
        assert adapter.ready() is expected
    assert paths == ['/v1/models']
