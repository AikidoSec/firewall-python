import pytest
from unittest.mock import MagicMock, patch
from .find_hostname_in_context import (
    find_hostname_in_context,
)  # Replace with the actual module name


# Mocking the dependencies
def mock_extract_strings_from_user_input_cached(user_input, source):
    return {"example_input": "path/to/payload"}


def mock_find_hostname_in_userinput(user_input, hostname, port):
    return user_input == hostname


# Test cases
def test_find_hostname_in_context_found(monkeypatch):
    # Arrange
    hostname = "example.com"
    context = MagicMock()
    context.cookies = "example.com"
    context.body = "another user input"
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)

    with patch(
        "aikido_zen.helpers.extract_strings_from_user_input.extract_strings_from_user_input_cached",
        side_effect=mock_extract_strings_from_user_input_cached,
    ):
        with patch(
            "aikido_zen.vulnerabilities.ssrf.find_hostname_in_userinput",
            side_effect=mock_find_hostname_in_userinput,
        ):  # Replace 'your_module' with the actual module name
            # Act
            result = find_hostname_in_context(hostname, context, 80)

            # Assert
            assert result == {
                "source": "cookies",
                "pathToPayload": ".",
                "payload": "example.com",
            }


def test_find_hostname_in_context_punycode_hostname(monkeypatch):
    hostname = "app.xn--loca-3b5a.aikido.dev"
    context = MagicMock()
    context.body = "app.locaḷ.aikido.dev"
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)

    with patch(
        "aikido_zen.helpers.extract_strings_from_user_input.extract_strings_from_user_input_cached",
        side_effect=mock_extract_strings_from_user_input_cached,
    ):
        with patch(
            "aikido_zen.vulnerabilities.ssrf.find_hostname_in_userinput",
            side_effect=mock_find_hostname_in_userinput,
        ):
            result = find_hostname_in_context(hostname, context, 80)

            assert result == {
                "source": "body",
                "pathToPayload": ".",
                "payload": "app.locaḷ.aikido.dev",
            }


def test_find_hostname_in_context_not_found(monkeypatch):
    # Arrange
    hostname = "notfound.com"
    context = MagicMock()
    context.body = "some user input"
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)

    with patch(
        "aikido_zen.helpers.extract_strings_from_user_input.extract_strings_from_user_input_cached",
        side_effect=mock_extract_strings_from_user_input_cached,
    ):
        with patch(
            "aikido_zen.vulnerabilities.ssrf.find_hostname_in_userinput",
            side_effect=mock_find_hostname_in_userinput,
        ):  # Replace 'your_module' with the actual module name
            # Act
            result = find_hostname_in_context(hostname, context, 80)

            # Assert
            assert result is None


def test_find_hostname_in_context_no_sources(monkeypatch):
    # Arrange
    hostname = "example.com"
    context = MagicMock()  # No attributes
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)

    # Act
    result = find_hostname_in_context(hostname, context, 80)

    # Assert
    assert result is None


# To run the tests, use the command: pytest <filename>.py


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
def test_doesnt_crash_with_invalid_hostname(invalid_input, monkeypatch):
    context = MagicMock()  # No attributes
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)
    result = find_hostname_in_context(invalid_input, context, 8080)
    assert result == None


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
def test_doesnt_crash_with_invalid_port(invalid_input, monkeypatch):
    context = MagicMock()  # No attributes
    monkeypatch.setattr("aikido_zen.context.get_current_context", lambda: None)
    result = find_hostname_in_context("https://example.com", context, invalid_input)
    assert result == None
