import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import pytest
from app.adapters import NemotronAnswerAdapter


@pytest.mark.parametrize('body,expected', [
    (b'{"data":[{"id":"synthetic-model"}]}', True),
    (b'{"data":[{"id":"other-model"}]}', False),
    (b'{"data":[]}', False),
    (b'not-json', False),
    (b' ' * 65_537, False),
])
def test_readiness_checks_exact_model_in_bounded_response(body, expected):
    paths=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            paths.append(self.path)
            self.send_response(200)
            self.send_header('Content-Length',str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        adapter=NemotronAnswerAdapter(f'http://127.0.0.1:{server.server_port}','synthetic-model',timeout_seconds=1)
        assert adapter.ready() is expected
        assert paths==['/v1/models']
    finally:
        server.shutdown();server.server_close();thread.join(timeout=2)
