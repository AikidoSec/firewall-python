import pytest
from .query_params_contain_dangerous_strings import (
    query_params_contain_dangerous_strings,
)
import aikido_zen.test_utils as test_utils


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
        ctx = test_utils.generate_context(query_value=s)
        assert query_params_contain_dangerous_strings(
            ctx
        ), f"Expected '{s}' to match patterns"


def test_does_not_detect():
    non_matching = ["google.de", "some-string", "1", ""]
    for s in non_matching:
        ctx = test_utils.generate_context(query_value=s)
        assert not query_params_contain_dangerous_strings(
            ctx
        ), f"Expected '{s}' to NOT match patterns"


def test_handles_empty_query_object():
    ctx = test_utils.generate_context(value="' or '1'='1")

    assert not query_params_contain_dangerous_strings(
        ctx
    ), "Expected empty query to NOT match injection patterns"
