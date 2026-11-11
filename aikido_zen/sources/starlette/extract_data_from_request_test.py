import json

import pytest

import aikido_zen.test_utils as test_utils
from aikido_zen.context import current_context
from aikido_zen.vulnerabilities.sql_injection.context_contains_sql_injection import (
    context_contains_sql_injection,
)
from .extract_data_from_request import extract_data_from_request

LEVELS_TOO_DEEP_TO_PARSE = 1_000_000


class FormRequest:
    def __init__(self, body, form):
        self._body = body
        self._form = form

    async def json(self):
        return json.loads(self._body)

    async def form(self):
        return self._form

    async def body(self):
        return self._body


class UnparsableFormRequest(FormRequest):
    async def form(self):
        raise ValueError("Invalid multipart data.")


class UrlencodedFormRequest(FormRequest):
    headers = {"content-type": "application/x-www-form-urlencoded"}


@pytest.fixture(autouse=True)
def run_around_tests():
    yield
    current_context.set(None)


@pytest.mark.asyncio
@pytest.mark.parametrize("opening", [b"[", b'{"a":'], ids=["list", "object"])
async def test_deeply_nested_json_body_does_not_hide_injection(opening):
    dog_name = "Dangerous Bobby', TRUE); -- "
    deep = opening * LEVELS_TOO_DEEP_TO_PARSE
    body = deep + b"&dog_name=" + dog_name.encode()
    form = {deep.decode(): "", "dog_name": dog_name}
    context = test_utils.generate_and_set_context()

    await extract_data_from_request(FormRequest(body, form))

    query = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % dog_name
    attack = context_contains_sql_injection(query, "execute", context, "postgres")
    assert attack["source"] == "body"
    assert attack["pathToPayload"] == ".dog_name"


@pytest.mark.asyncio
async def test_form_that_cannot_be_parsed_is_kept_as_the_raw_body():
    context = test_utils.generate_and_set_context()

    await extract_data_from_request(UnparsableFormRequest(b"x' OR 1=1 -- ", None))

    assert context.body == "x' OR 1=1 -- "


@pytest.mark.asyncio
async def test_json_body_sent_as_form_is_parsed_once(mocker):
    loads = mocker.spy(json, "loads")
    form = {'{"a":"': "", "id": "1' OR 1=1 -- \"}"}
    context = test_utils.generate_and_set_context()

    await extract_data_from_request(
        UrlencodedFormRequest(b'{"a":"&id=1\' OR 1=1 -- "}', form)
    )

    assert loads.call_count == 1
    assert context.body == [{"a": "&id=1' OR 1=1 -- "}, form]
