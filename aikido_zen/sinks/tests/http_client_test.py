import http.client
import http.server
import threading
from unittest.mock import patch

import pytest

import aikido_zen.sinks.http_client


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
