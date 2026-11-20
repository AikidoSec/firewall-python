import pytest
from .context_contains_sql_injection import context_contains_sql_injection
import aikido_zen.test_utils as test_utils
from aikido_zen.context import Context


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
    context = test_utils.generate_context(value=invalid_input)
    result = context_contains_sql_injection(
        sql=invalid_input,
        operation="mysqlclient.query",
        context=context,
        dialect="mysql",
    )
    assert result == {}


JSON_STRING_BODIES = [b'"1\' OR 1=1 -- \\u0041"', '"1\' OR 1=1 -- \\u0041"']
JSON_STRING_BODY_IDS = ["raw_text", "json_string_decoded_once"]


@pytest.mark.parametrize("body", JSON_STRING_BODIES, ids=JSON_STRING_BODY_IDS)
def test_injection_in_the_body_text_the_app_uses_is_detected(body):
    app_value = '"1\' OR 1=1 -- \\u0041"'
    context = Context(body=body)
    query = f"SELECT * FROM users WHERE id = '{app_value}'"

    attack = context_contains_sql_injection(
        query, "mysqlclient.query", context, "mysql"
    )

    assert attack["source"] == "body"
    assert attack["pathToPayload"] == "."
    assert attack["payload"] == app_value


@pytest.mark.parametrize("body", JSON_STRING_BODIES, ids=JSON_STRING_BODY_IDS)
def test_injection_in_the_parsed_body_is_still_detected(body):
    context = Context(body=body)
    query = f"SELECT * FROM users WHERE id = '{context.body}'"

    attack = context_contains_sql_injection(
        query, "mysqlclient.query", context, "mysql"
    )

    assert attack["source"] == "body"
    assert attack["payload"] == "1' OR 1=1 -- A"
