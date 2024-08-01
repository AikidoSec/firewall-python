import pytest
from unittest.mock import MagicMock, patch
import copy
import json

# Assuming the classes are defined in a module named aikido
from aikido_firewall.sinks.psycopg2 import MutableAikidoConnection, MutableAikidoCursor


# Mock functions for context and logging
def mock_get_current_context():
    return {"user": "test_user"}


def mock_context_contains_sql_injection(sql, source, context, db):
    return False  # Change this to True to test SQL injection handling


def mock_get_comms():
    comms = MagicMock()
    comms.send_data_to_bg_process = MagicMock()
    comms.poll_config = MagicMock(return_value=False)
    return comms


# Test for MutableConnection
def test_mutable__connection():
    # Create a mock former connection
    mock_cursor = MagicMock()
    mock_cursor.execute = MagicMock(return_value="result")

    mock_former_conn = MagicMock()
    mock_former_conn.cursor = MagicMock(return_value=mock_cursor)

    # Create an instance of MutableConnection
    connection = MutableAikidoConnection(mock_former_conn)

    # Test cursor method
    cursor = connection.cursor()
    assert isinstance(cursor, MutableAikidoCursor)
    assert cursor._former_cursor == mock_cursor

    # Test accessing other attributes
    mock_former_conn.some_attribute = "value"
    assert connection.some_attribute == "value"


# Test for MutableCursor
@patch(
    "aikido_firewall.context.get_current_context", side_effect=mock_get_current_context
)
@patch(
    "aikido_firewall.vulnerabilities.sql_injection.context_contains_sql_injection",
    side_effect=mock_context_contains_sql_injection,
)
@patch("aikido_firewall.background_process.get_comms", side_effect=mock_get_comms)
def test_mutable_aikido_cursor(
    mock_get_context, mock_context_injection, mock_get_comms
):
    # Create a mock former cursor
    mock_execute = MagicMock(return_value="execute_result")
    mock_former_cursor = MagicMock()
    mock_former_cursor.execute = mock_execute

    # Create an instance of MutableAikidoCursor
    cursor = MutableAikidoCursor(mock_former_cursor)

    # Test execute method
    result = cursor.execute("SELECT * FROM table")
    assert result == "execute_result"

    # Test accessing other attributes
    mock_former_cursor.some_method = MagicMock(return_value="some_value")
    assert cursor.some_method() == "some_value"
