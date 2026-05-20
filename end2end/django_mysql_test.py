import time
import pytest
import requests
from .server.check_events_from_mock import fetch_events_from_mock, validate_started_event, filter_on_event_type, validate_heartbeat

# e2e tests for django_mysql sample app
base_url_fw = "http://localhost:8080/app"
base_url_nofw = "http://localhost:8081/app"

def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], ["django", "mysqlclient"])

def test_safe_response_with_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(base_url_fw + "/create", data={'dog_name': dog_name})
    assert res.status_code == 200

def test_safe_response_without_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(base_url_nofw + "/create", data={'dog_name': dog_name})
    assert res.status_code == 200


def test_dangerous_response_with_firewall():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(base_url_fw + "/create", data={'dog_name': dog_name})
    assert res.status_code == 500
    time.sleep(5) # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")
    
    assert len(attacks) == 1
    del attacks[0]["attack"]["stack"]
    assert attacks[0]["attack"] == {
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {
            'dialect': 'mysql',
            'sql': 'INSERT INTO sample_app_dogs (dog_name, dog_boss) VALUES ("Dangerous bobby", 1); -- ", "N/A")'
        },
        'operation': 'MySQLdb.Cursor.execute',
        'pathToPayload': '.dog_name.[0]',
        'payload': '"Dangerous bobby\\", 1); -- "',
        'source': "body",
        'user': None
    }

def test_dangerous_response_with_firewall_shell():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.get(base_url_fw + "/shell/ls -la")
    assert res.status_code == 500
    time.sleep(5) # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")
    
    assert len(attacks) == 2
    del attacks[0] # Previous attack
    del attacks[0]["attack"]["stack"]
    assert attacks[0]["attack"] == {
        "blocked": True,
        "kind": "shell_injection",
        'metadata': {'command': 'ls -la'},
        'operation': 'subprocess.Popen',
        'pathToPayload': '.[0]',
        'payload': '"ls -la"',
        'source': "route_params",
        'user': None
    }

def test_dangerous_response_without_firewall():
    dog_name = 'Dangerous bobby", 1); -- '
    res = requests.post(base_url_nofw + "/create", data={'dog_name': dog_name})
    assert res.status_code == 200

def test_initial_heartbeat():
    time.sleep(55)  # Sleep 5 + 55 seconds for heartbeat
    events = fetch_events_from_mock("http://localhost:5000")
    heartbeat_events = filter_on_event_type(events, "heartbeat")
    assert len(heartbeat_events) == 1
    validate_heartbeat(
        heartbeat_events[0],
        routes=[{
            "apispec": {
                'body': {
                    'type': 'form-urlencoded',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'dog_name': {
                                'items': {'type': 'string'},
                                'type': 'array'
                            }
                        }
                    }
                },
                'query': None,
                'auth': None
            },
            "hits": 1,
            "hits_delta_since_sync": 0,
            "method": "POST",
            "path": "/app/create"
        }],
        packages={'wrapt', 'asgiref', 'aikido_zen', 'django', 'sqlparse', 'mysqlclient', 'regex'}
    )
    req_stats = heartbeat_events[0]["stats"]["requests"]
    assert req_stats["aborted"] == 0
    assert req_stats["rateLimited"] == 0
    assert req_stats["attacksDetected"] == {"blocked": 2, "total": 2}
    assert req_stats["attackWaves"] == {"total": 0, "blocked": 0}


# --- AIKIDO-5RDTZW1V regression: invalid UTF-8 bytes must not bypass detection ---

def test_bypass_invalid_utf8_bytes_path_traversal():
    # An attacker prepends \xff (invalid UTF-8) to a path traversal payload.
    # Before the fix, decode("utf-8") raised UnicodeDecodeError and the body was
    # never stored, so the firewall saw nothing.  After the fix the body is decoded
    # with errors="replace" and the traversal is still detected.
    body = b"\xff/../../../../../etc/passwd"
    res = requests.post(base_url_fw + "/read", data=body)
    assert res.status_code == 500

    time.sleep(5)
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 3
    assert attacks[2]["attack"]["kind"] == "path_traversal"
    assert attacks[2]["attack"]["blocked"] is True
    assert attacks[2]["attack"]["source"] == "body"


# --- AIKIDO-B3YABOSP regression: surrogate bytes in JSON must not bypass detection ---

def test_bypass_surrogate_bytes_sql_injection():
    # Surrogate bytes (\xed\xa0\x80) make decode("utf-8") raise, so the old code
    # never parsed the body as JSON and the SQL injection payload was invisible.
    # After the fix, json.loads(bytes) is tried first (it uses surrogatepass internally)
    # so the dict is extracted and the injection is caught when the cursor executes.
    body = b'{"dog_name": "Dangerous bobby\\", 1); -- ", "bypass": "\xed\xa0\x80"}'
    res = requests.post(base_url_fw + "/json-sql", data=body)
    assert res.status_code == 500

    time.sleep(5)
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")

    assert len(attacks) == 4
    assert attacks[3]["attack"]["kind"] == "sql_injection"
    assert attacks[3]["attack"]["blocked"] is True
    assert attacks[3]["attack"]["source"] == "body"
