import pytest
from .check_context_for_shell_injection import check_context_for_shell_injection
import aikido_zen.test_utils as test_utils


def test_detect_shell_injection():
    context = test_utils.generate_context(value="www.example`whoami`.com")
    result = check_context_for_shell_injection(
        command="binary --domain www.example`whoami`.com",
        operation="child_process.exec",
        context=context,
    )

    expected = {
        "operation": "child_process.exec",
        "kind": "shell_injection",
        "source": "body",
        "pathToPayload": ".key1",
        "metadata": {
            "command": "binary --domain www.example`whoami`.com",
        },
        "payload": "www.example`whoami`.com",
    }

    assert result == expected


def test_detect_shell_injection_from_route_params():
    context = test_utils.generate_context(query_value="www.example`whoami`.com")
    result = check_context_for_shell_injection(
        command="binary --domain www.example`whoami`.com",
        operation="child_process.exec",
        context=context,
    )

    expected = {
        "operation": "child_process.exec",
        "kind": "shell_injection",
        "source": "query",
        "pathToPayload": ".key1",
        "metadata": {
            "command": "binary --domain www.example`whoami`.com",
        },
        "payload": "www.example`whoami`.com",
    }

    assert result == expected


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
def test_doesnt_crash_with_invalid_command(invalid_input):
    context = test_utils.generate_context(value=invalid_input)
    result = check_context_for_shell_injection(
        command=invalid_input,
        operation="child_process.exec",
        context=context,
    )
    assert result == {}
