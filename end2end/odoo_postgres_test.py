import json
import time
import urllib.parse
import uuid
import xmlrpc.client
from xml.sax.saxutils import quoteattr

import pytest
import requests

from .server.check_events_from_mock import (
    fetch_events_from_mock,
    filter_on_event_type,
    validate_started_event,
)

# e2e tests for the odoo-postgres sample app (real Odoo in Docker)
base_url_fw = "http://localhost:8120"
base_url_nofw = "http://localhost:8121"
mock_url = "http://localhost:5000"
databases = {base_url_fw: "odoo_zen", base_url_nofw: "odoo_without_zen"}

dog_name = "Dangerous Bobby', TRUE); -- "
both = pytest.mark.parametrize("base_url", [base_url_fw, base_url_nofw])


def jsonrpc(base_url, path, params, session=requests):
    res = session.post(
        base_url + path,
        json={"jsonrpc": "2.0", "method": "call", "params": params, "id": 1},
    )
    assert res.status_code == 200
    return res.json()


def error_name(body):
    return body.get("error", {}).get("data", {}).get("name")


def dog_count(base_url, name=None):
    params = {"name": name} if name else {}
    return int(requests.get(base_url + "/zen/dogs/count", params=params).text)


def file_exists(base_url, name):
    return requests.get(base_url + "/zen/files/" + name).text == "yes"


def test_firewall_started_okay():
    events = fetch_events_from_mock(mock_url)
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) >= 1
    validate_started_event(started_events[0], None, os_name="Linux")


@pytest.mark.parametrize(
    "send",
    [
        lambda url, value: requests.get(
            url + "/zen/shell/query", params={"command": value}
        ),
        lambda url, value: requests.post(
            url + "/zen/shell/form", data={"command": value}
        ),
        lambda url, value: requests.get(
            url + "/zen/shell/header", headers={"X-Command": value}
        ),
        lambda url, value: requests.get(
            url + "/zen/shell/cookie", cookies={"command": value}
        ),
    ],
    ids=["query", "form", "header", "cookie"],
)
def test_shell_injection(send):
    name = "shell-" + uuid.uuid4().hex
    attack = "true && touch /tmp/zen_files/" + name
    assert send(base_url_fw, attack).status_code == 500
    assert not file_exists(base_url_fw, name)

    assert send(base_url_nofw, attack).status_code == 200
    assert file_exists(base_url_nofw, name)


@both
@pytest.mark.parametrize(
    "path, name", [("/zen/dog", "Bobby"), ("/zen/dog_safe", dog_name)]
)
def test_safe_jsonrpc_call_is_not_blocked(base_url, path, name):
    assert jsonrpc(base_url, path, {"dog_name": name})["result"] == name


def test_sql_injection_over_jsonrpc():
    before = dog_count(base_url_fw)
    body = jsonrpc(base_url_fw, "/zen/dog", {"dog_name": dog_name})
    assert error_name(body) == "aikido_zen.errors.AikidoSQLInjection"
    assert dog_count(base_url_fw) == before

    before = dog_count(base_url_nofw)
    body = jsonrpc(base_url_nofw, "/zen/dog", {"dog_name": dog_name})
    assert body["result"] == dog_name
    assert dog_count(base_url_nofw) == before + 1


@pytest.mark.parametrize(
    "send",
    [
        lambda url: requests.get(
            url
            + "/zen/dog/owner/"
            + urllib.parse.quote("o'k", safe="")
            + "/"
            + urllib.parse.quote("x;', TRUE) -- ", safe="")
        ),
        lambda url: requests.post(
            url + "/zen/dog/text",
            data=dog_name.encode(),
            headers={"Content-Type": "text/plain"},
        ),
        lambda url: requests.post(
            url + "/zen/dog/xml",
            data=f"<dogs><dog name={quoteattr(dog_name)}/></dogs>".encode(),
            headers={"Content-Type": "application/xml"},
        ),
    ],
    ids=["route", "text-body", "xml-body"],
)
def test_sql_injection_over_http(send):
    before = dog_count(base_url_fw)
    assert send(base_url_fw).status_code == 500
    assert dog_count(base_url_fw) == before

    before = dog_count(base_url_nofw)
    assert send(base_url_nofw).status_code == 200
    assert dog_count(base_url_nofw) == before + 1


def test_sql_injection_over_call_kw():
    call = {
        "model": "zen.test.dog",
        "method": "create_unsafe",
        "args": [dog_name],
        "kwargs": {},
    }
    for base_url, blocked in [(base_url_fw, True), (base_url_nofw, False)]:
        session = requests.Session()
        jsonrpc(
            base_url,
            "/web/session/authenticate",
            {"db": databases[base_url], "login": "admin", "password": "admin"},
            session,
        )
        before = dog_count(base_url)
        body = jsonrpc(base_url, "/web/dataset/call_kw", call, session)
        if blocked:
            assert error_name(body) == "aikido_zen.errors.AikidoSQLInjection"
            assert dog_count(base_url) == before
        else:
            assert body["result"] is True
            assert dog_count(base_url) == before + 1


def test_sql_injection_over_xmlrpc():
    for base_url, blocked in [(base_url_fw, True), (base_url_nofw, False)]:
        db = databases[base_url]
        uid = xmlrpc.client.ServerProxy(base_url + "/xmlrpc/2/common").authenticate(
            db, "admin", "admin", {}
        )
        models = xmlrpc.client.ServerProxy(base_url + "/xmlrpc/2/object")
        before = dog_count(base_url)
        args = [db, uid, "admin", "zen.test.dog", "create_unsafe", [dog_name]]
        if blocked:
            with pytest.raises(xmlrpc.client.Fault, match="AikidoSQLInjection"):
                models.execute_kw(*args)
            assert dog_count(base_url) == before
        else:
            models.execute_kw(*args)
            assert dog_count(base_url) == before + 1


def test_sql_injection_over_external_jsonrpc():
    for base_url, blocked in [(base_url_fw, True), (base_url_nofw, False)]:
        db = databases[base_url]
        login = {"service": "common", "method": "login", "args": [db, "admin", "admin"]}
        uid = jsonrpc(base_url, "/jsonrpc", login)["result"]
        call = {
            "service": "object",
            "method": "execute_kw",
            "args": [db, uid, "admin", "zen.test.dog", "create_unsafe", [dog_name]],
        }
        before = dog_count(base_url)
        body = jsonrpc(base_url, "/jsonrpc", call)
        if blocked:
            assert error_name(body) == "aikido_zen.errors.AikidoSQLInjection"
            assert dog_count(base_url) == before
        else:
            assert body["result"] is True
            assert dog_count(base_url) == before + 1


def test_uploaded_file_name_traversal():
    upload = {"upload": ("../../tmp/zen-uploaded.txt", b"x")}
    assert requests.post(base_url_fw + "/zen/upload", files=upload).status_code == 500
    assert requests.post(base_url_nofw + "/zen/upload", files=upload).status_code == 200


def test_blocked_ip_does_not_reach_the_controller():
    headers = {"X-Forwarded-For": "1.2.3.4"}
    name = "blocked-" + uuid.uuid4().hex

    def post(base_url):
        return requests.post(base_url + "/zen/dog/text", data=name, headers=headers)

    # Each worker gets the firewall lists from its first sync with the background process.
    deadline = time.monotonic() + 60
    while (res := post(base_url_fw)).status_code != 403:
        assert time.monotonic() < deadline, res.text
        time.sleep(1)
    before = dog_count(base_url_fw, name)
    res = post(base_url_fw)
    assert res.status_code == 403
    assert (
        res.text
        == "Your IP address is blocked due to geo restrictions (Your IP: 1.2.3.4)"
    )
    assert dog_count(base_url_fw, name) == before

    assert post(base_url_nofw).status_code == 200


def test_attacks_detected():
    time.sleep(5)  # Wait for attacks to be reported
    attacks = [
        event["attack"]
        for event in filter_on_event_type(
            fetch_events_from_mock(mock_url), "detected_attack"
        )
    ]
    found = {(attack["kind"], attack["source"]) for attack in attacks}

    assert {
        ("sql_injection", "body"),
        ("sql_injection", "route_params"),
        ("shell_injection", "query"),
        ("shell_injection", "body"),
        ("shell_injection", "headers"),
        ("shell_injection", "cookies"),
        ("path_traversal", "body"),
    } <= found
    assert all(attack["blocked"] for attack in attacks)
    text_body = [
        attack
        for attack in attacks
        if attack["kind"] == "sql_injection" and attack["pathToPayload"] == "."
    ]
    assert text_body and text_body[0]["payload"] == json.dumps(dog_name)
