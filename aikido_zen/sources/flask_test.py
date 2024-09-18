import pytest
import signal
from unittest.mock import patch
import aikido_zen.sources.flask
from aikido_zen.background_process.comms import reset_comms
from aikido_zen.context import current_context, get_current_context

sample_environ = {
    "REQUEST_METHOD": "POST",
    "HTTP_HEADER_1": "header 1 value",
    "HTTP_HEADER_2": "Header 2 value",
    "RANDOM_VALUE": "Random value",
    "HTTP_COOKIE": "sessionId=abc123xyz456;",
    "wsgi.url_scheme": "https",
    "HTTP_HOST": "example.com",
    "PATH_INFO": "/hello",
    "QUERY_STRING": "user=JohnDoe&age=30&age=35",
    "CONTENT_TYPE": "application/x-www-form-urlencoded",
    "REMOTE_ADDR": "198.51.100.23",
}


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException


signal.signal(signal.SIGALRM, timeout_handler)


def test_flask_all_3_func():
    with patch(
        "aikido_zen.sources.functions.request_handler.request_handler"
    ) as mock_request_handler:
        reset_comms()
        current_context.set(None)
        mock_request_handler.return_value = None

        from flask import Flask

        app = Flask(__name__)
        try:
            signal.alarm(1)
            app(sample_environ, lambda x, y: x)
            app.run()
        except TimeoutException:
            pass
        assert get_current_context().method == "POST"
        assert get_current_context().body == None
        assert get_current_context().headers == {
            "COOKIE": "sessionId=abc123xyz456;",
            "HEADER_1": "header 1 value",
            "HEADER_2": "Header 2 value",
            "HOST": "example.com",
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
        }
        calls = mock_request_handler.call_args_list
        assert len(calls) == 3
        assert calls[0][1]["stage"] == "init"
        assert calls[1][1]["stage"] == "pre_response"
        assert calls[2][1]["stage"] == "post_response"
        assert calls[2][1]["status_code"] == 404


def test_startup_flask():
    reset_comms()
    from flask import Flask

    app = Flask(__name__)
    try:
        signal.alarm(1)
        app.run()
    except TimeoutException:
        pass
