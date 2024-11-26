import pytest
from aikido_zen.context import Context
from .context_contains_sql_injection import context_contains_sql_injection


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
        123,  # Integer
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
def test_doesnt_crash_with_invalid_sql(invalid_input):
    context = Context2()
    result = context_contains_sql_injection(
        sql=invalid_input,
        operation="mysqlclient.query",
        context=context,
        dialect="mysql",
    )
    assert result == {}
