import pytest
from .context_contains_sql_injection import context_contains_sql_injection
import aikido_zen.test_utils as test_utils


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
