import pytest
from aikido_firewall.context import Context
from .check_context_for_ssrf import check_context_for_ssrf


class Context2(Context):
    def __init__(self):
        self.cookies = {}
        self.headers = {}
        self.remote_address = "ip"
        self.method = "POST"
        self.url = "url"
        self.body = {}
        self.query = {
            "domain": "www.example`whoami`.com",
        }
        self.source = "express"
        self.route = "/"
        self.parsed_userinput = {}


@pytest.mark.parametrize(
    "invalid_input",
    [
        None,
        123456789,  # Integer
        45.67,  # Float
        [],  # Empty list
        [1, 2, 3],  # List of integers
        {},  # Empty dictionary
        {"key": "value"},  # Dictionary
        set(),  # Empty set
        {1, 2, 3},  # Set of integers
        object(),  # Instance of a generic object
        lambda x: x,  # Lambda function
        (1, 2),  # Tuple
        b"bytes",  # Bytes
    ],
)
def test_doesnt_crash_with_invalid_hostname(invalid_input):
    context = Context2()
    result = check_context_for_ssrf(
        hostname=invalid_input,
        port=8080,
        operation="http.putrequest",
        context=context,
    )
    assert result == {}


@pytest.mark.parametrize(
    "invalid_input",
    [
        None,
        "test",  # String
        45.67,  # Float
        [],  # Empty list
        [1, 2, 3],  # List of integers
        {},  # Empty dictionary
        {"key": "value"},  # Dictionary
        set(),  # Empty set
        {1, 2, 3},  # Set of integers
        object(),  # Instance of a generic object
        lambda x: x,  # Lambda function
        (1, 2),  # Tuple
        b"bytes",  # Bytes
    ],
)
def test_doesnt_crash_with_invalid_port(invalid_input):
    context = Context2()
    result = check_context_for_ssrf(
        hostname="example.com",
        port=invalid_input,
        operation="http.putrequest",
        context=context,
    )
    assert result == {}
