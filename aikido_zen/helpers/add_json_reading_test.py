import json

import pytest

import aikido_zen.test_utils as test_utils
from aikido_zen.vulnerabilities.nosql_injection.check_context import (
    check_context_for_nosql_injection,
)
from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)
from .add_json_reading import add_json_reading

form = {"field": ["value"]}
JSON_TOO_DEEP_TO_PARSE = b"[" * 1_000_000
DOC = '{"username": {"$regex": ".*"}}'
PARSED_DOC = {"username": {"$regex": ".*"}}


def test_form_body_stays_the_form_without_parsing_it(mocker):
    loads = mocker.spy(json, "loads")
    assert add_json_reading(form, b"field=value") is form
    loads.assert_not_called()


@pytest.mark.parametrize(
    "raw_body, parsed",
    [
        (DOC.encode(), PARSED_DOC),
        (b'[{"$where": "1"}]', [{"$where": "1"}]),
        (b'"1\' OR 1=1"', "1' OR 1=1"),
        (b' \t\r\n{"a": 1}', {"a": 1}),
        (b"\xef\xbb\xbf" + DOC.encode(), PARSED_DOC),
        (DOC.encode("utf-16"), PARSED_DOC),
        (DOC.encode("utf-16-be"), PARSED_DOC),
        (DOC.encode("utf-32"), PARSED_DOC),
    ],
    ids=[
        "object",
        "array",
        "string",
        "leading_whitespace",
        "utf8_bom",
        "utf16",
        "utf16_be",
        "utf32",
    ],
)
def test_json_body_adds_the_json_reading(raw_body, parsed):
    assert add_json_reading(form, raw_body) == [parsed, form]


@pytest.mark.parametrize(
    "raw_body",
    [
        b"{not json",
        JSON_TOO_DEEP_TO_PARSE,
        b'{"a": "\xff"}',
        b"",
        b"123",
        "é=1&b=2".encode(),
    ],
    ids=[
        "invalid_json",
        "too_deep",
        "invalid_utf8",
        "empty",
        "number",
        "non_ascii_form",
    ],
)
def test_body_that_is_not_json_stays_the_form(raw_body):
    assert add_json_reading(form, raw_body) is form


def test_nosql_injection_in_the_json_reading_is_detected():
    raw_body = b'{"username": {"$regex": ".*"}}'
    context = test_utils.generate_context()
    context.body = add_json_reading({raw_body.decode(): [""]}, raw_body)
    attack = check_context_for_nosql_injection(
        context, "find", {"name": {"$regex": ".*"}}
    )
    assert attack["source"] == "body"
    assert attack["pathToPayload"] == ".[0].username"


def test_sql_injection_in_the_form_reading_is_still_detected():
    raw_body = b'{"a":"&id=1\' OR 1=1 -- "}'
    context = test_utils.generate_context()
    context.body = add_json_reading(
        {'{"a":"': [""], "id": ["1' OR 1=1 -- \"}"]}, raw_body
    )
    query = "SELECT * FROM users WHERE id = '1' OR 1=1 -- \"}'"
    attack = context_contains_sql_injection(query, "select", context, "sqlite")
    assert attack["source"] == "body"
    assert attack["pathToPayload"] == ".[1].id.[0]"
