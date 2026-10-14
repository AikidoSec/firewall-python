import time
import pytest
import requests
from .server.check_events_from_mock import fetch_events_from_mock, filter_on_event_type

# e2e tests for the flask_postgres_xml routes that parse through expat
base_url_fw = "http://localhost:8092"
base_url_nofw = "http://localhost:8093"
routes = ["/xml_post_minidom", "/xml_post_sax", "/xml_post_pulldom"]

payload = "Malicious dog', TRUE); -- "
character_references = "".join(f"&#{ord(c)};" for c in payload)


@pytest.mark.parametrize("route", routes)
def test_safe_response_with_firewall(route):
    res = requests.post(base_url_fw + route, data="<dogs><dog>Bobby</dog></dogs>")
    assert res.status_code == 200


@pytest.mark.parametrize("route", routes)
def test_safe_response_without_firewall(route):
    res = requests.post(base_url_nofw + route, data="<dogs><dog>Bobby</dog></dogs>")
    assert res.status_code == 200


def attacks_on(route):
    events = fetch_events_from_mock("http://localhost:5000")
    return [
        a for a in filter_on_event_type(events, "detected_attack")
        if a["request"]["route"] == route
    ]


@pytest.mark.parametrize("route", routes)
@pytest.mark.parametrize("dog", [payload, character_references])
def test_dangerous_response_with_firewall(route, dog):
    attacks_before = len(attacks_on(route))
    res = requests.post(base_url_fw + route, data=f"<dogs><dog>{dog}</dog></dogs>")
    assert res.status_code == 500

    time.sleep(5) # Wait for attack to be reported
    attacks = attacks_on(route)[attacks_before:]

    assert len(attacks) == 1
    del attacks[0]["attack"]["stack"]
    # The raw and the stripped text both match, and either can be reported first.
    assert attacks[0]["attack"].pop("payload") in (
        "\"Malicious dog', TRUE); -- \"",
        "\"Malicious dog', TRUE); --\"",
    )

    assert attacks[0]["attack"] == {
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {
            'dialect': "postgres",
            'sql': "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Malicious dog', TRUE); -- ', FALSE)"
        },
        'operation': "psycopg2.Connection.Cursor.execute",
        'pathToPayload': ".dog.[0]",
        'source': "xml",
        'user': None
    }


@pytest.mark.parametrize("route", routes)
@pytest.mark.parametrize("dog", [payload, character_references])
def test_dangerous_response_without_firewall(route, dog):
    res = requests.post(base_url_nofw + route, data=f"<dogs><dog>{dog}</dog></dogs>")
    assert res.status_code == 200
