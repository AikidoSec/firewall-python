"""
Test file for flask.py
"""

# pylint: disable=unused-import
import pytest
import aikido_firewall.sources.flask as aik_flask

example_environ = {
    "wsgi.version": (1, 0),
    "wsgi.url_scheme": "http",
    "wsgi.input": None,
    "wsgi.errors": None,
    "wsgi.multithread": True,
    "wsgi.multiprocess": False,
    "wsgi.run_once": False,
    "werkzeug.socket": None,
    "SERVER_SOFTWARE": "Werkzeug/3.0.3",
    "REQUEST_METHOD": "GET",
    "SCRIPT_NAME": "",
    "PATH_INFO": "/",
    "QUERY_STRING": "",
    "REQUEST_URI": "/",
    "RAW_URI": "/",
    "REMOTE_ADDR": "127.0.0.1",
    "REMOTE_PORT": 58920,
    "SERVER_NAME": "127.0.0.1",
    "SERVER_PORT": "5000",
    "SERVER_PROTOCOL": "HTTP/1.1",
    "HTTP_HOST": "localhost:5000",
    "HTTP_CONNECTION": "keep-alive",
    "HTTP_COOKIE": "test=value; test2=value2",
}


def test_aikido_middleware_init(mocker):
    """Testing for AikidoMiddleware __init__ function"""
    app = mocker.MagicMock()
    middleware = aik_flask.AikidoMiddleware(app)
    assert middleware.app == app
