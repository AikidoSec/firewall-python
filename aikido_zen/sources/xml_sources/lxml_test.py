from aikido_zen.context import Context, get_current_context
import aikido_zen.sources.xml_sources.lxml
import lxml.etree as ET

# Sample XML string for testing
XML_STRING = """<?xml version="1.0"?>
<root>
    <child attr="chill" test="test1" smth="2" smthelse="2">
        <name smth="2" test="test2">Test Name</name>
        <value ok="boomer">42</value>
    </child>
</root>
"""


def parse_xml(xml_string):
    """Parse the given XML string and return the root element."""
    try:
        root = ET.fromstring(xml_string)
        return root
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML: {e}")


def set_context(body):
    Context(
        req={
            "REQUEST_METHOD": "GET",
            "HTTP_HEADER_1": "header 1 value",
            "HTTP_HEADER_2": "Header 2 value",
            "RANDOM_VALUE": "Random value",
            "HTTP_COOKIE": "sessionId=abc123xyz456;",
            "wsgi.url_scheme": "http",
            "HTTP_HOST": "localhost:8080",
            "PATH_INFO": "/hello",
            "QUERY_STRING": "user=JohnDoe&age=30&age=35",
            "CONTENT_TYPE": "application/json",
            "REMOTE_ADDR": "198.51.100.23",
            "HTTP_USER_AGENT": "Mozilla/5.0",
        },
        body=body,
        source="django",
    ).set_as_current_context()


def test_parse_xml_with_random_context():
    """Test the XML parsing function."""
    set_context("Body falalalala")
    root = parse_xml(XML_STRING)

    # Check XML parser still works
    assert root[0].find("name").text == "Test Name"

    # Check that no xml attribute was set on body
    context = get_current_context()
    assert context.xml == {}


def test_parse_xml_with_set_context():
    """Test the XML parsing function."""
    set_context(body=XML_STRING)
    root = parse_xml(XML_STRING)

    # Check XML parser still works
    assert root[0].find("name").text == "Test Name"

    # Check that no xml attribute was set on body
    context = get_current_context()
    assert context.xml == {
        "attr": {"chill"},
        "smth": {"2"},
        "smthelse": {"2"},
        "test": {"test1"},
    }
