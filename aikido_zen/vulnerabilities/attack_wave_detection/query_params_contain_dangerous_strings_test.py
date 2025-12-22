import pytest
from .query_params_contain_dangerous_strings import (
    query_params_contain_dangerous_strings,
)


class Context:
    def __init__(self, query=None, body=None):
        self.remote_address = "::1"
        self.method = "GET"
        self.url = "http://localhost:4000/test"
        self.query = query or {
            "test": "",
            "utmSource": "newsletter",
            "utmMedium": "electronicmail",
            "utmCampaign": "test",
            "utmTerm": "sql_injection",
        }
        self.headers = {"content-type": "application/json"}
        self.body = body or {}
        self.cookies = {}
        self.route_params = {}
        self.source = "express"
        self.route = "/test"


def get_test_context(query):
    return Context(
        query={
            "test": query,
            **{
                "utmSource": "newsletter",
                "utmMedium": "electronicmail",
                "utmCampaign": "test",
                "utmTerm": "sql_injection",
            },
        }
    )


def test_detects_injection_patterns():
    test_strings = [
        "' or '1'='1",
        "1: SELECT * FROM users WHERE '1'='1'",
        "', information_schema.tables",
        "1' sleep(5)",
        "WAITFOR DELAY 1",
        "../etc/passwd",
    ]
    for s in test_strings:
        ctx = get_test_context(s)
        assert query_params_contain_dangerous_strings(
            ctx
        ), f"Expected '{s}' to match patterns"


def test_does_not_detect():
    non_matching = ["google.de", "some-string", "1", ""]
    for s in non_matching:
        ctx = get_test_context(s)
        assert not query_params_contain_dangerous_strings(
            ctx
        ), f"Expected '{s}' to NOT match patterns"


def test_handles_empty_query_object():
    ctx = Context(query={})
    assert not query_params_contain_dangerous_strings(
        ctx
    ), "Expected empty query to NOT match injection patterns"
