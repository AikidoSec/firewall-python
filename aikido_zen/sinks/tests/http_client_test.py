import http.client
import http.server
import threading
import urllib.request
from unittest.mock import patch

import pytest

import aikido_zen.sinks.http_client
from aikido_zen.context import current_context, get_current_context
from aikido_zen.test_utils import generate_and_set_context
from aikido_zen.thread.thread_cache import get_cache


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    get_cache().reset()
    current_context.set(None)


@pytest.mark.parametrize("url_as_keyword", [False, True])
def test_getresponse_reports_the_url_given_to_putrequest(url_as_keyword):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    try:
        with patch(
            "aikido_zen.sinks.http_client.handle_http_response"
        ) as handle_http_response:
            conn = http.client.HTTPConnection("127.0.0.1", port)
            if url_as_keyword:
                conn.putrequest("GET", url="/path?x=1")
            else:
                conn.putrequest("GET", "/path?x=1")
            conn.endheaders()
            conn.getresponse().read()
            conn.close()
    finally:
        server.shutdown()

    source = handle_http_response.call_args.kwargs["source"]
    assert source.geturl() == f"http://127.0.0.1:{port}/path?x=1"


def start_server(location=None):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302 if location else 200)
            if location:
                self.send_header("Location", location)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def test_records_every_hop_of_a_followed_redirect_chain():
    server_c, port_c = start_server()
    server_b, port_b = start_server(f"http://127.0.0.1:{port_c}/end")
    server_a, port_a = start_server(f"http://127.0.0.1:{port_b}/next")
    generate_and_set_context(value=f"http://127.0.0.1:{port_a}/start")
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port_a}/start").read()
    finally:
        for server in (server_a, server_b, server_c):
            server.shutdown()

    redirects = [
        (r["source"].port, r["destination"].port)
        for r in get_current_context().outgoing_req_redirects
    ]

    assert redirects == [(port_a, port_b), (port_b, port_c)]
