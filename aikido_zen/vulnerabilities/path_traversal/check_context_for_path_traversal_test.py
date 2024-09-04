import pytest
from .check_context_for_path_traversal import check_context_for_path_traversal


# Sample unsafe context for testing
class UnsafeContext:
    cookies = {}
    headers = {}
    remote_address = "1.1.1.1"
    method = "POST"
    url = "http://localhost:8080/"
    query = {}
    body = {"path": "../file"}
    source = "flask"
    route = None


class SafeContext:
    url = "/_next/static/RjAvHy_jB1ciRT_xBrSyI/_ssgManifest.js"
    method = "GET"
    headers = {
        "host": "localhost:3000",
        "connection": "keep-alive",
        "pragma": "no-cache",
        "cache-control": "no-cache",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "sec-ch-ua-platform": '"macOS"',
        "accept": "*/*",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-dest": "script",
        "referer": "http://localhost:3000/",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "nl,en;q=0.9,en-US;q=0.8",
        "cookie": "Phpstorm-8262f4a6=6a1925f9-2f0e-45ea-8336-a6988d56b1aa",
        "x-forwarded-host": "localhost:3000",
        "x-forwarded-port": "3000",
        "x-forwarded-proto": "http",
        "x-forwarded-for": "127.0.0.1",
    }
    route = None
    query = {}
    source = "flask"
    cookies = {
        "Phpstorm-8262f4a6": "6a1925f9-2f0e-45ea-8336-a6988d56b1aa",
    }
    body = None
    remote_address = "127.0.0.1"


def test_detects_path_traversal_from_route_parameter(monkeypatch):
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)
    result = check_context_for_path_traversal("../file/test.txt", "op", UnsafeContext())
    assert result == {
        "operation": "op",
        "kind": "path_traversal",
        "source": "body",
        "pathToPayload": ".path",
        "metadata": {
            "filename": "../file/test.txt",
        },
        "payload": "../file",
    }


def test_does_not_flag_safe_operation(monkeypatch):
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)

    filename = "../../web/spec-extension/cookies"
    operation = "path.normalize"
    result = check_context_for_path_traversal(filename, operation, SafeContext())
    assert len(result) == 0


def test_detects_path_traversal_with_buffer(monkeypatch):
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)

    filename = b"../file/test.txt"
    result = check_context_for_path_traversal(filename, "op", UnsafeContext())
    assert result == {
        "operation": "op",
        "kind": "path_traversal",
        "source": "body",
        "pathToPayload": ".path",
        "metadata": {
            "filename": "../file/test.txt",
        },
        "payload": "../file",
    }


def test_detects_path_traversal_with_url(monkeypatch):
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)

    filename = "file:///../file/test.txt"
    result = check_context_for_path_traversal(filename, "op", UnsafeContext())
    assert result == {
        "operation": "op",
        "kind": "path_traversal",
        "source": "body",
        "pathToPayload": ".path",
        "metadata": {
            "filename": "/../file/test.txt",
        },
        "payload": "../file",
    }


def test_ignores_non_utf8_buffer(monkeypatch):
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)

    filename = bytes([0x80, 0x81, 0x82, 0x83])
    result = check_context_for_path_traversal(filename, "op", UnsafeContext())
    assert len(result) == 0


def test_ignores_invalid_filename_type(monkeypatch):
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)

    filename = object()
    result = check_context_for_path_traversal(filename, "op", UnsafeContext())
    assert len(result) == 0
