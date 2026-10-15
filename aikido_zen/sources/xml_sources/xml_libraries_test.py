import aikido_zen.sources.xml_sources.expat
import aikido_zen.sources.xml_sources.lxml
import aikido_zen.sources.xml_sources.xml
import aikido_zen.helpers.extract_data_from_xml_body
from aikido_zen.context import Context, current_context, get_current_context
from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)

import io
import pytest
import xml.dom.minidom
import xml.dom.pulldom
import xml.etree.ElementTree as ET
import xml.sax
from xml.sax.handler import ContentHandler
import defusedxml.ElementTree
import defusedxml.minidom
import defusedxml.pulldom
import defusedxml.sax
import lxml.etree
import xmltodict

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
        },
        body=body,
        source="flask",
    ).set_as_current_context()


def is_reported(value):
    sql = f"SELECT * FROM users WHERE id = '{value}'"
    return context_contains_sql_injection(sql, "op", get_current_context(), "mysql")


def stream(body):
    return io.BytesIO(body.encode())


def sax_parse_string(parse_string):
    return lambda body: parse_string(body.encode(), ContentHandler())


def consume(iterator):
    for _ in iterator:
        pass


PARSERS = {
    "ET.fromstring": ET.fromstring,
    "ET.XML": ET.XML,
    "ET.fromstringlist": lambda body: ET.fromstringlist([body]),
    "ET.parse": lambda body: ET.parse(stream(body)),
    "ET.iterparse": lambda body: consume(ET.iterparse(stream(body))),
    "lxml.fromstring": lxml.etree.fromstring,
    "lxml.XML": lxml.etree.XML,
    "lxml.fromstringlist": lambda body: lxml.etree.fromstringlist([body]),
    "lxml.parse": lambda body: lxml.etree.parse(stream(body)),
    "lxml.iterparse": lambda body: consume(lxml.etree.iterparse(stream(body))),
    "minidom.parseString": xml.dom.minidom.parseString,
    "minidom.parse": lambda body: xml.dom.minidom.parse(stream(body)),
    "pulldom.parseString": lambda body: consume(xml.dom.pulldom.parseString(body)),
    "sax.parseString": sax_parse_string(xml.sax.parseString),
    "sax.parse": lambda body: xml.sax.parse(stream(body), ContentHandler()),
    "xmltodict.parse": xmltodict.parse,
    "defusedxml.ElementTree.fromstring": defusedxml.ElementTree.fromstring,
    "defusedxml.ElementTree.parse": lambda body: defusedxml.ElementTree.parse(
        stream(body)
    ),
    "defusedxml.ElementTree.iterparse": lambda body: consume(
        defusedxml.ElementTree.iterparse(stream(body))
    ),
    "defusedxml.minidom.parseString": defusedxml.minidom.parseString,
    "defusedxml.pulldom.parseString": lambda body: consume(
        defusedxml.pulldom.parseString(body)
    ),
    "defusedxml.sax.parseString": sax_parse_string(defusedxml.sax.parseString),
}

BODIES = {
    "element text": f"<xml><id>{PAYLOAD}</id></xml>",
    "root attribute": f'<xml value="{PAYLOAD}"><id/></xml>',
    "child attribute": f'<xml><id value="{PAYLOAD}"/></xml>',
    "nested attribute": f'<xml><a><b><id value="{PAYLOAD}"/></b></a></xml>',
    "text after an element": f"<xml><a/>{PAYLOAD}</xml>",
    "cdata": f"<xml><id><![CDATA[{PAYLOAD}]]></id></xml>",
    "entity": "<xml><id>1&apos; OR 1=1 -- </id></xml>",
    "character references": "<xml><id>"
    + "".join(f"&#{ord(c)};" for c in PAYLOAD)
    + "</id></xml>",
}


@pytest.mark.parametrize("body", BODIES.values(), ids=BODIES.keys())
@pytest.mark.parametrize("parser", PARSERS.values(), ids=PARSERS.keys())
def test_payload_in_the_body_is_reported(parser, body):
    set_context(body)
    parser(body)

    assert is_reported(PAYLOAD)


@pytest.mark.parametrize("parser", PARSERS.values(), ids=PARSERS.keys())
def test_xml_that_is_not_the_body_is_not_collected(parser):
    set_context("<other>body</other>")
    parser(f"<xml><id>{PAYLOAD}</id></xml>")

    assert get_current_context().xml == {}


@pytest.mark.parametrize(
    "iterparse",
    [ET.iterparse, lxml.etree.iterparse, defusedxml.ElementTree.iterparse],
    ids=["ET", "lxml", "defusedxml"],
)
@pytest.mark.parametrize("event", ["start", "end"])
def test_iterparse_values_are_scanned_inside_the_loop(iterparse, event):
    body = f"<dogs><dog>safe value</dog><dog>{PAYLOAD}</dog></dogs>"
    set_context(body)
    results = []

    for _, element in iterparse(stream(body), events=(event,)):
        if element.tag == "dog":
            results.append(bool(is_reported(element.text)))
            element.clear()

    assert results == [False, True]


@pytest.mark.parametrize(
    "iterparse",
    [ET.iterparse, lxml.etree.iterparse, defusedxml.ElementTree.iterparse],
    ids=["ET", "lxml", "defusedxml"],
)
@pytest.mark.parametrize("events", [("start",), ("end",)], ids=["start", "end"])
def test_iterparse_text_after_an_element_is_collected(iterparse, events):
    body = "<dogs><f>" + "x" * 40000 + f"</f><dog/>{PAYLOAD}</dogs>"
    set_context(body)
    consume(iterparse(stream(body), events=events))

    assert is_reported(PAYLOAD)


@pytest.mark.parametrize(
    "parse",
    [
        lambda body: defusedxml.ElementTree.parse(stream(body)),
        lambda body: ET.parse(
            stream(body), parser=defusedxml.ElementTree.DefusedXMLParser()
        ),
        lambda body: ET.fromstring(
            body, parser=defusedxml.ElementTree.DefusedXMLParser()
        ),
    ],
    ids=["defusedxml.parse", "ET.parse", "ET.fromstring"],
)
def test_expat_based_parser_is_collected_once(parse, mocker):
    body = f"<xml><id>{PAYLOAD}</id></xml>"
    set_context(body)
    tree_walk = mocker.spy(
        aikido_zen.helpers.extract_data_from_xml_body, "add_elements_to_context"
    )
    parse(body)

    assert tree_walk.call_count == 0
    assert is_reported(PAYLOAD)


def test_expat_based_parser_made_outside_a_request_is_still_collected():
    current_context.set(None)
    parser = defusedxml.ElementTree.DefusedXMLParser()
    body = f"<xml><id>{PAYLOAD}</id></xml>"
    set_context(body)
    ET.fromstring(body, parser=parser)

    assert is_reported(PAYLOAD)


@pytest.mark.parametrize(
    "zen_function",
    [
        (aikido_zen.sources.xml_sources.expat.Collector, "add"),
        (aikido_zen.helpers.extract_data_from_xml_body, "add_elements_to_context"),
        (aikido_zen.helpers.extract_data_from_xml_body.BodyMatcher, "continues_body"),
    ],
    ids=["expat add", "tree walk", "body comparison"],
)
@pytest.mark.parametrize("parser", PARSERS.values(), ids=PARSERS.keys())
def test_app_still_parses_when_zen_raises(parser, zen_function, monkeypatch):
    def raise_error(*args, **kwargs):
        raise RuntimeError("error inside Zen")

    monkeypatch.setattr(*zen_function, raise_error)
    body = f"<xml><id>{PAYLOAD}</id></xml>"
    set_context(body)

    parser(body)


def test_parse_of_a_large_body_is_collected():
    body = "<xml>" + "<a>filler</a>" * 10000 + f"<id>{PAYLOAD}</id></xml>"
    set_context(body)
    ET.parse(stream(body))

    assert is_reported(PAYLOAD)


@pytest.mark.parametrize(
    "fromstring, parsers",
    [
        (
            ET.fromstring,
            [
                lambda body: ET.parse(stream(body)),
                lambda body: consume(ET.iterparse(stream(body))),
            ],
        ),
        (
            lxml.etree.fromstring,
            [
                lambda body: lxml.etree.parse(stream(body)),
                lambda body: consume(lxml.etree.iterparse(stream(body))),
            ],
        ),
    ],
    ids=["ET", "lxml"],
)
def test_parse_and_iterparse_store_what_fromstring_stores(fromstring, parsers):
    body = f'<xml value="{PAYLOAD}"><a>text<!-- -->more</a>tail<b c="d"/></xml>'
    set_context(body)
    fromstring(body)
    from_string = get_current_context().xml

    for parse in parsers:
        set_context(body)
        parse(body)

        assert get_current_context().xml == from_string
