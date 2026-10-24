import json
from io import BytesIO

import pytest
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request as WerkzeugRequest

from .body import extract_body


class OdooRequest:
    def __init__(self, httprequest):
        self.httprequest = httprequest

    def get_json_data(self):
        return json.loads(self.httprequest.get_data(as_text=True))


def test_extract_form_preserves_duplicate_values_without_reading_uploads():
    environ = EnvironBuilder(
        method="POST",
        data={
            "tag": ["first", "second"],
            "upload": (BytesIO(b"file contents"), "example.txt"),
        },
    ).get_environ()
    request = OdooRequest(WerkzeugRequest(environ))

    body = extract_body(request, "http")

    assert body == {"tag": ["first", "second"]}
    assert request.httprequest.form.getlist("tag") == ["first", "second"]
    assert request.httprequest.files["upload"].stream.tell() == 0


@pytest.mark.parametrize("routing_type", ["json", "jsonrpc", "json2"])
def test_extract_json_keeps_the_full_envelope_and_cached_request_data(routing_type):
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {"command": "echo test", "context": {"lang": "en_US"}},
        "id": 7,
    }
    encoded_payload = json.dumps(payload).encode()
    environ = EnvironBuilder(
        method="POST",
        data=encoded_payload,
        content_type="application/json",
    ).get_environ()
    request = OdooRequest(WerkzeugRequest(environ))

    assert extract_body(request, routing_type) == payload
    assert request.httprequest.get_data(cache=True) == encoded_payload


def test_extract_unstructured_body_uses_the_cached_request_data():
    payload = b"plain text body"
    environ = EnvironBuilder(
        method="POST",
        data=payload,
        content_type="text/plain",
    ).get_environ()
    request = OdooRequest(WerkzeugRequest(environ))

    assert extract_body(request, "http") == payload
    assert request.httprequest.get_data(cache=True) == payload


def test_malformed_json_remains_available_for_odoo_to_parse():
    payload = b'{"invalid":'
    environ = EnvironBuilder(
        method="POST",
        data=payload,
        content_type="application/json",
    ).get_environ()
    request = OdooRequest(WerkzeugRequest(environ))

    with pytest.raises(json.JSONDecodeError):
        extract_body(request, "json")
    with pytest.raises(json.JSONDecodeError):
        request.get_json_data()

    assert request.httprequest.get_data(cache=True) == payload
