import pytest
from aikido_firewall.helpers.try_parse_as_json import try_parse_as_json
from aikido_firewall.context.parse_cookies import parse_cookies
from .get_context_from_gateway_event import get_context_from_gateway_event


# Mock the try_parse_as_json and parse_cookies functions
def mock_try_parse_as_json(body):
    if body == '{"valid": "json"}':
        return {"valid": "json"}
    return None


def mock_parse_cookies(cookie_header):
    if cookie_header:
        return {"session": "abc123"}
    return {}


# Use pytest's monkeypatch to replace the original functions with the mocks
@pytest.fixture(autouse=True)
def mock_functions(monkeypatch):
    monkeypatch.setattr(
        "aikido_firewall.helpers.try_parse_as_json.try_parse_as_json",
        mock_try_parse_as_json,
    )
    monkeypatch.setattr("aikido_firewall.context.parse_cookies", mock_parse_cookies)


def test_get_context_from_gateway_event_valid():
    event = {
        "httpMethod": "POST",
        "requestContext": {"identity": {"sourceIp": "192.168.1.1"}},
        "headers": {"Content-Type": "application/json", "cookie": "session=abc123"},
        "body": '{"valid": "json"}',
        "pathParameters": {},
        "queryStringParameters": {},
        "resource": "/test",
    }
    expected_output = {
        "url": None,
        "method": "POST",
        "remote_address": "192.168.1.1",
        "body": {"valid": "json"},
        "headers": {"Content-Type": "application/json", "cookie": "session=abc123"},
        "route_params": {},
        "query": {},
        "cookies": {"session": "abc123"},
        "source": "lambda/gateway",
        "route": "/test",
    }
    assert get_context_from_gateway_event(event) == expected_output


def test_get_context_from_gateway_event_no_body():
    event = {
        "httpMethod": "POST",
        "requestContext": {"identity": {"sourceIp": "192.168.1.1"}},
        "headers": {"Content-Type": "application/json"},
        "body": None,
        "pathParameters": {},
        "queryStringParameters": {},
        "resource": "/test",
    }
    expected_output = {
        "url": None,
        "method": "POST",
        "remote_address": "192.168.1.1",
        "body": None,
        "headers": {"Content-Type": "application/json"},
        "route_params": {},
        "query": {},
        "cookies": {},
        "source": "lambda/gateway",
        "route": "/test",
    }
    assert get_context_from_gateway_event(event) == expected_output


def test_get_context_from_gateway_event_non_json_content_type():
    event = {
        "httpMethod": "POST",
        "requestContext": {"identity": {"sourceIp": "192.168.1.1"}},
        "headers": {"Content-Type": "text/plain"},
        "body": '{"valid": "json"}',
        "pathParameters": {},
        "queryStringParameters": {},
        "resource": "/test",
    }
    expected_output = {
        "url": None,
        "method": "POST",
        "remote_address": "192.168.1.1",
        "body": None,
        "headers": {"Content-Type": "text/plain"},
        "route_params": {},
        "query": {},
        "cookies": {},
        "source": "lambda/gateway",
        "route": "/test",
    }
    assert get_context_from_gateway_event(event) == expected_output


def test_get_context_from_gateway_event_missing_headers():
    event = {
        "httpMethod": "GET",
        "requestContext": {"identity": {"sourceIp": "192.168.1.1"}},
        "body": '{"valid": "json"}',
        "pathParameters": {},
        "queryStringParameters": {},
        "resource": "/test",
    }
    expected_output = {
        "url": None,
        "method": "GET",
        "remote_address": "192.168.1.1",
        "body": None,
        "headers": {},
        "route_params": {},
        "query": {},
        "cookies": {},
        "source": "lambda/gateway",
        "route": "/test",
    }
    assert get_context_from_gateway_event(event) == expected_output


def test_get_context_from_gateway_event_with_cookies():
    event = {
        "httpMethod": "GET",
        "requestContext": {"identity": {"sourceIp": "192.168.1.1"}},
        "headers": {
            "Content-Type": "application/json",
            "cookie": "session=abc123; user=xyz789",
        },
        "body": '{"valid": "json"}',
        "pathParameters": {},
        "queryStringParameters": {},
        "resource": "/test",
    }
    expected_output = {
        "url": None,
        "method": "GET",
        "remote_address": "192.168.1.1",
        "body": {"valid": "json"},
        "headers": {
            "Content-Type": "application/json",
            "cookie": "session=abc123; user=xyz789",
        },
        "route_params": {},
        "query": {},
        "cookies": {"session": "abc123", "user": "xyz789"},
        "source": "lambda/gateway",
        "route": "/test",
    }
    assert get_context_from_gateway_event(event) == expected_output
