import pytest
from unittest.mock import MagicMock
import aikido_firewall.context as ctx
from .extract_data_from_xml_body import (
    extract_data_from_xml_body,
)  # Replace 'your_module' with the actual module name


@pytest.fixture
def mock_context():
    """Fixture to mock the context."""
    mock_ctx = MagicMock()
    mock_ctx.body = "valid_input"
    mock_ctx.xml = {}  # Initialize with an empty dictionary
    ctx.get_current_context = MagicMock(return_value=mock_ctx)
    return mock_ctx


def test_extract_data_from_xml_body_valid_input(mock_context):
    """Test with valid user input and root_element."""
    user_input = "valid_input"
    root_element = [
        {"attr1": "value1", "attr2": "value2"},
        {"attr1": "value3", "attr3": "value4"},
    ]

    extract_data_from_xml_body(user_input, root_element)

    assert mock_context.xml == {
        "attr1": {"value1", "value3"},
        "attr2": {"value2"},
        "attr3": {"value4"},
    }


def test_extract_data_from_xml_body_invalid_user_input(mock_context):
    """Test with invalid user input."""
    user_input = "invalid_input"
    root_element = [{"attr1": "value1"}]

    extract_data_from_xml_body(user_input, root_element)

    assert mock_context.xml == {}


def test_extract_data_from_xml_body_empty_root_element(mock_context):
    """Test with an empty root_element."""
    user_input = "valid_input"
    root_element = []

    extract_data_from_xml_body(user_input, root_element)

    assert mock_context.xml == {}


def test_extract_data_from_xml_body_non_string_context_body(mock_context):
    """Test with non-string context body."""
    mock_context.body = 123  # Set body to a non-string value
    user_input = "valid_input"
    root_element = [{"attr1": "value1"}]

    extract_data_from_xml_body(user_input, root_element)

    assert mock_context.xml == {}


def test_extract_data_from_xml_body_multiple_calls(mock_context):
    """Test multiple calls with the same user input."""
    user_input = "valid_input"
    root_element1 = [{"attr1": "value1"}]
    root_element2 = [{"attr1": "value2"}]

    extract_data_from_xml_body(user_input, root_element1)
    extract_data_from_xml_body(user_input, root_element2)

    assert mock_context.xml == {"attr1": {"value1", "value2"}}


def test_extract_data_from_xml_body_duplicate_attributes(mock_context):
    """Test with duplicate attributes in root_element."""
    user_input = "valid_input"
    root_element = [
        {"attr1": "value1"},
        {"attr1": "value1"},  # Duplicate
        {"attr2": "value2"},
    ]

    extract_data_from_xml_body(user_input, root_element)

    assert mock_context.xml == {"attr1": {"value1"}, "attr2": {"value2"}}


def test_extract_data_from_xml_body_no_attributes(mock_context):
    """Test with elements that have no attributes."""
    user_input = "valid_input"
    root_element = [{}]

    extract_data_from_xml_body(user_input, root_element)

    assert mock_context.xml == {}


def test_extract_data_from_xml_body_context_set_as_current(mock_context):
    """Test if context.set_as_current_context is called."""
    user_input = "valid_input"
    root_element = [{"attr1": "value1"}]

    extract_data_from_xml_body(user_input, root_element)

    mock_context.set_as_current_context.assert_called_once()
