import aikido_zen.sources.xml_sources.expat
from aikido_zen.context import Context, current_context, get_current_context
from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)

import io
import pytest
import xml.dom.minidom
import xml.dom.pulldom
import xml.sax
from xml.parsers import expat
from xml.sax.handler import ContentHandler
import defusedxml.minidom
import defusedxml.sax
import xmltodict

XML_STRING = """<?xml version="1.0"?>
<root>
    <child attr="chill">
        <name test="test2">Test Name</name>
        <value>42</value>
    </child>
</root>
"""

PAYLOAD = "1' OR 1=1 -- "


def set_context(body):
    Context(
        req={
            "REQUEST_METHOD": "POST",
            "wsgi.url_scheme": "http",
            "HTTP_HOST": "localhost:8080",
            "PATH_INFO": "/hello",
            "QUERY_STRING": "",
            "CONTENT_TYPE": "application/xml",
            "REMOTE_ADDR": "198.51.100.23",
            "HTTP_USER_AGENT": "Mozilla/5.0",
        },
        body=body,
        source="flask",
    ).set_as_current_context()


def is_reported(value):
    sql = f"SELECT * FROM users WHERE id = '{value}'"
    return context_contains_sql_injection(sql, "op", get_current_context(), "mysql")


class CollectText(ContentHandler):
    def __init__(self):
        super().__init__()
        self.pieces = []

    def characters(self, content):
        self.pieces.append(content)


def sax_text(parse_string, body):
    handler = CollectText()
    parse_string(body.encode(), handler)
    return "".join(handler.pieces)


def pulldom_text(body):
    events = xml.dom.pulldom.parseString(body)
    for event, node in events:
        if event == xml.dom.pulldom.START_ELEMENT and node.tagName == "id":
            events.expandNode(node)
            node.normalize()
            return node.firstChild.data


def minidom_text(parse_string, body):
    return parse_string(body).getElementsByTagName("id")[0].firstChild.data


APP_TEXT = {
    "minidom": lambda b: minidom_text(xml.dom.minidom.parseString, b),
    "defusedxml.minidom": lambda b: minidom_text(defusedxml.minidom.parseString, b),
    "sax": lambda b: sax_text(xml.sax.parseString, b),
    "defusedxml.sax": lambda b: sax_text(defusedxml.sax.parseString, b),
    "pulldom": pulldom_text,
    "xmltodict": lambda b: xmltodict.parse(b)["xml"]["id"],
}


def test_parse_xml_with_random_context():
    set_context("Body falalalala")
    document = xml.dom.minidom.parseString(XML_STRING)

    assert document.getElementsByTagName("name")[0].firstChild.data == "Test Name"
    assert get_current_context().xml == {}


def test_parse_xml_with_set_context():
    set_context(body=XML_STRING)
    document = xml.dom.minidom.parseString(XML_STRING)

    assert document.getElementsByTagName("name")[0].firstChild.data == "Test Name"
    assert get_current_context().xml == {
        "attr": {"chill"},
        "name": {"Test Name"},
        "test": {"test2"},
        "value": {"42"},
    }


def test_parse_xml_bytes_with_set_context():
    body = XML_STRING.encode("utf-8")
    set_context(body=body)
    xml.dom.minidom.parseString(body)

    assert get_current_context().xml["name"] == {"Test Name"}


def test_parse_xml_without_context():
    current_context.set(None)
    parser = expat.ParserCreate()

    assert type(parser) is expat.XMLParserType


def test_parser_still_behaves_like_an_expat_parser():
    set_context(body=XML_STRING)
    parser = expat.ParserCreate()

    def start_element(name, attributes):
        pass

    parser.StartElementHandler = start_element

    assert isinstance(parser, expat.XMLParserType)
    assert parser.StartElementHandler is start_element


def test_parse_file_is_not_collected():
    set_context(body=XML_STRING)
    xmltodict.parse(io.BytesIO(XML_STRING.encode()))

    assert get_current_context().xml == {}


def test_file_read_in_chunks_by_the_library_is_collected():
    set_context(body=XML_STRING)
    xml.dom.minidom.parse(io.BytesIO(XML_STRING.encode()))

    assert get_current_context().xml["name"] == {"Test Name"}


@pytest.mark.parametrize("library", APP_TEXT)
@pytest.mark.parametrize(
    "body",
    [
        f"<xml><id>{PAYLOAD}</id></xml>",
        f"<xml><id><![CDATA[{PAYLOAD}]]></id></xml>",
        "<xml><id>1&apos; OR 1=1 -- </id></xml>",
        "<xml><id>" + "".join(f"&#{ord(c)};" for c in PAYLOAD) + "</id></xml>",
        "<xml><id>1'\nOR 1=1 -- </id></xml>",
    ],
)
def test_element_text_the_app_reads_is_reported(library, body):
    set_context(body=body)
    value = APP_TEXT[library](body)

    assert is_reported(value)


def test_text_split_by_a_comment_is_reported_for_each_reading():
    body = "<xml><id>1' OR 1=1 -- <!-- -->x</id></xml>"
    set_context(body=body)
    first_text = minidom_text(xml.dom.minidom.parseString, body)
    joined_text = xmltodict.parse(body)["xml"]["id"]

    assert first_text == "1' OR 1=1 -- "
    assert joined_text == "1' OR 1=1 -- x"
    assert is_reported(first_text)
    assert is_reported(joined_text)


def test_text_split_by_a_child_element_is_reported_joined():
    body = "<xml><id>1' OR <b/>1=1 -- </id></xml>"
    set_context(body=body)
    joined_text = xmltodict.parse(body)["xml"]["id"]["#text"]

    assert joined_text == "1' OR 1=1 --"
    assert is_reported(joined_text)


def test_values_parsed_after_a_query_are_scanned():
    body = f"<xml><a>safe value</a><id>{PAYLOAD}</id></xml>"
    set_context(body=body)
    results = []

    class QueryPerElement(ContentHandler):
        def characters(self, content):
            results.append(bool(is_reported(content)))

    xml.sax.parseString(body.encode(), QueryPerElement())

    assert results == [False, True]


def test_character_references_are_scanned_inside_characters():
    body = "<xml><id>" + "".join(f"&#{ord(c)};" for c in PAYLOAD) + "</id></xml>"
    set_context(body=body)
    results = []

    class QueryWhileBuilding(ContentHandler):
        value = ""

        def characters(self, content):
            self.value += content
            if self.value == PAYLOAD:
                results.append(bool(is_reported(self.value)))

    xml.sax.parseString(body.encode(), QueryWhileBuilding())

    assert results == [True]


def test_equal_value_from_another_element_is_kept():
    body = "<xml><id>1'</id><id>&#49;&#39;&#32;x</id></xml>"
    set_context(body=body)
    xml.sax.parseString(body.encode(), ContentHandler())

    assert get_current_context().xml["id"] == {"1'", "1' x"}


def test_character_references_arrive_as_one_piece():
    set_context(body=XML_STRING)
    parser = expat.ParserCreate()
    pieces = []
    parser.CharacterDataHandler = pieces.append
    parser.Parse("<xml>" + "&#65;" * 100 + "</xml>", True)

    assert pieces == ["A" * 100]


def test_app_can_turn_buffer_text_off():
    set_context(body=XML_STRING)
    parser = expat.ParserCreate()
    parser.buffer_text = False
    pieces = []
    parser.CharacterDataHandler = pieces.append
    parser.Parse("<xml>&#65;&#66;</xml>", True)

    assert pieces == ["A", "B"]


def test_each_chunk_is_compared_once():
    body = "<xml>" + "<a>filler</a>" * 10000 + f"<id>{PAYLOAD}</id></xml>"
    set_context(body=body)
    compared = []

    class CountingBody(str):
        def startswith(self, prefix, start=0, *args):
            compared.append(len(prefix))
            return str.startswith(self, prefix, start, *args)

    get_current_context().body = CountingBody(body)
    xml.sax.parse(io.BytesIO(body.encode()), ContentHandler())

    assert len(compared) > 1
    assert sum(compared) == len(body)
    assert is_reported(PAYLOAD)


def test_latin_1_body_is_collected():
    body = f'<?xml version="1.0" encoding="ISO-8859-1"?><xml><id>caf\xe9 {PAYLOAD}</id></xml>'
    raw = body.encode("latin-1")
    set_context(body=raw)
    value = minidom_text(xml.dom.minidom.parseString, raw)

    assert value == f"caf\xe9 {PAYLOAD}"
    assert is_reported(value)
