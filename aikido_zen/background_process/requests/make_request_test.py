from unittest.mock import patch

from aikido_zen.background_process.get_common_agent_headers import (
    get_common_agent_headers,
)
from aikido_zen.background_process.requests.make_request import make_request


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self):
        return 200

    def info(self):
        return {}

    def read(self):
        return b""


def test_make_request_sends_agent_headers():
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        return _Response()

    expected = get_common_agent_headers()
    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        make_request(
            "GET",
            "https://example.test/api",
            1,
            headers={"Authorization": "token"},
        )

    headers = {
        name.lower(): value for name, value in captured["request"].header_items()
    }
    assert headers["authorization"] == "token"
    for name, value in expected.items():
        assert headers[name.lower()] == value
