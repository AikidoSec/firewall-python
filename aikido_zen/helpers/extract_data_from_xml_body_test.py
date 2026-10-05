import pytest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET
import aikido_zen.context as ctx
from .extract_data_from_xml_body import (
    extract_data_from_xml_body,
)  # Replace 'your_module' with the actual module name


@pytest.fixture
def mock_context():
    mock_ctx = MagicMock()
    mock_ctx.body = "valid_input"
    mock_ctx.xml = {}  # Initialize with an empty dictionary
    return mock_ctx


def test_does_not_crash_when_context_none(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=None):
        user_input = "valid_input"
        root_element = ET.fromstring(
            '<root><a attr1="value1" attr2="value2"/><b attr1="value3" attr3="value4"/></root>'
        )

        extract_data_from_xml_body(user_input, root_element)


def test_extract_data_from_xml_body_valid_input(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element = ET.fromstring(
            '<root><a attr1="value1" attr2="value2"/><b attr1="value3" attr3="value4"/></root>'
        )

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {
            "attr1": {"value1", "value3"},
            "attr2": {"value2"},
            "attr3": {"value4"},
        }


def test_extract_data_from_xml_body_invalid_user_input(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "invalid_input"
        root_element = ET.fromstring('<root><a attr1="value1"/></root>')

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {}


def test_extract_data_from_xml_body_empty_root_element(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element = ET.fromstring("<root></root>")

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {}


def test_extract_data_from_xml_body_non_string_context_body(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        mock_context.body = 123  # Set body to a non-string value
        user_input = "valid_input"
        root_element = ET.fromstring('<root><a attr1="value1"/></root>')

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {}


def test_extract_data_from_xml_body_multiple_calls(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element1 = ET.fromstring('<root><a attr1="value1"/></root>')
        root_element2 = ET.fromstring('<root><a attr1="value2"/></root>')

        extract_data_from_xml_body(user_input, root_element1)
        extract_data_from_xml_body(user_input, root_element2)

        assert mock_context.xml == {"attr1": {"value1", "value2"}}


def test_extract_data_from_xml_body_duplicate_attributes(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element = ET.fromstring(
            '<root><a attr1="value1"/><b attr1="value1"/><c attr2="value2"/></root>'
        )

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {"attr1": {"value1"}, "attr2": {"value2"}}


def test_extract_data_from_xml_body_no_attributes(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element = ET.fromstring("<root><a/></root>")

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {}


def test_extract_data_from_xml_body_element_text(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element = ET.fromstring("<root><id>value1</id></root>")

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {"id": {"value1"}}


def test_extract_data_from_xml_body_indented_element_text(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element = ET.fromstring("<root><id>\n    value1\n  </id></root>")

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {"id": {"\n    value1\n  ", "value1"}}


def test_extract_data_from_xml_body_text_between_elements(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element = ET.fromstring("<root>before<a/>after</root>")

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {"root": {"before"}, "a": {"after"}}


def test_extract_data_from_xml_body_root_attributes(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element = ET.fromstring('<root attr1="value1"><a/></root>')

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {"attr1": {"value1"}}


def test_extract_data_from_xml_body_nested_attributes(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element = ET.fromstring('<root><a><b attr1="value1"/></a></root>')

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {"attr1": {"value1"}}


@pytest.mark.parametrize(
    "root_element", [None, "not an element", [{"attr1": "value1"}]]
)
def test_extract_data_from_xml_body_invalid_root_element(mock_context, root_element):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        extract_data_from_xml_body("valid_input", root_element)

        assert mock_context.xml == {}


def test_extract_data_from_xml_body_comments_and_processing_instructions(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        parser = ET.XMLParser(
            target=ET.TreeBuilder(insert_comments=True, insert_pis=True)
        )
        root_element = ET.fromstring(
            "<root><!-- comment --><?pi data?><a>value1</a></root>", parser
        )

        extract_data_from_xml_body("valid_input", root_element)

        assert mock_context.xml == {"a": {"value1"}}


def test_extract_data_from_xml_body_context_set_as_current(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = "valid_input"
        root_element = ET.fromstring('<root><a attr1="value1"/></root>')

        extract_data_from_xml_body(user_input, root_element)

        mock_context.set_as_current_context.assert_called_once()


def test_extract_data_from_xml_body_bytes_user_input(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = b"valid_input"
        root_element = ET.fromstring(
            '<root><a attr1="value1"/><b attr2="value2"/></root>'
        )

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {"attr1": {"value1"}, "attr2": {"value2"}}


def test_extract_data_from_xml_body_bytes_invalid_user_input(mock_context):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        user_input = b"invalid_input"
        root_element = ET.fromstring('<root><a attr1="value1"/></root>')

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {}


@pytest.mark.parametrize(
    "user_input", [bytearray(b"valid_input"), memoryview(b"valid_input")]
)
def test_extract_data_from_xml_body_byteslike_user_input(mock_context, user_input):
    with patch("aikido_zen.context.get_current_context", return_value=mock_context):
        root_element = ET.fromstring('<root><a attr1="value1"/></root>')

        extract_data_from_xml_body(user_input, root_element)

        assert mock_context.xml == {"attr1": {"value1"}}


def test_extract_data_from_xml_body_bytes_invalid_utf8_matches_body():
    body = b'<xml><item id="1\xff">1\xff</item></xml>'
    context = ctx.Context(body=body, source="test")
    root_element = ET.fromstring(context.body)
    context.set_as_current_context()
    try:
        extract_data_from_xml_body(body, root_element)

        assert context.xml == {"id": {"1�"}, "item": {"1�"}}
    finally:
        ctx.current_context.set(None)
