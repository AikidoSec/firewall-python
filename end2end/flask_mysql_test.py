from django_mysql.test_sql_attack import test_sql_attack
from utils.EventHandler import EventHandler
from utils.test_safe_vs_unsafe_payloads import test_safe_vs_unsafe_payloads

# e2e tests for flask_mysql sample app
payloads_sql = {
    "safe": {"dog_name": "Bobby Tables"},
    "unsafe": {"dog_name": 'Dangerous bobby", 1); -- '},
    "json": False  # Form data
}
urls = {
    "enabled": "http://localhost:8086",
    "disabled": "http://localhost:8087"
}

event_handler = EventHandler()
event_handler.reset()

test_safe_vs_unsafe_payloads(payloads_sql, urls, route="/create")
print("✅ Tested safe/unsafe payloads on /create")

test_sql_attack(
    event_handler,
    sql='INSERT INTO dogs (dog_name, isAdmin) VALUES ("Dangerous bobby", 1); -- ", 0)',
    operation="pymysql.Cursor.execute"
)
print("✅ Tested accurate reporting of an attack")

"""
def test_dangerous_response_with_firewall_route_params():
    events = fetch_events_from_mock("http://localhost:5000")
    assert len(filter_on_event_type(events, "detected_attack")) == 1
    res = requests.get(base_url_fw + "/shell/ls -la")
    assert res.status_code == 500

    time.sleep(5) # Wait for attack to be reported
    events = fetch_events_from_mock("http://localhost:5000")
    attacks = filter_on_event_type(events, "detected_attack")
    
    assert len(attacks) == 2
    del attacks[0]
    assert attacks[0]["attack"]["blocked"] == True
    assert attacks[0]["attack"]["kind"] == "shell_injection"
    assert attacks[0]["attack"]['metadata']['command'] == 'ls -la'
    assert attacks[0]["attack"]["operation"] == 'subprocess.Popen'
    assert attacks[0]["attack"]["pathToPayload"] == '.command'
    assert attacks[0]["attack"]["payload"] == '"ls -la"'
    assert attacks[0]["attack"]["source"] == "route_params"
    assert attacks[0]["attack"]["user"]["id"] == "123"
    assert attacks[0]["attack"]["user"]["name"] == "John Doe"
"""

"""
def test_ratelimiting_1_route():
    # First request :
    res = requests.get(base_url_fw + "/test_ratelimiting_1")
    assert res.status_code == 200
    # Second request :
    res = requests.get(base_url_fw + "/test_ratelimiting_1")
    assert res.status_code == 200
    # Third request :
    res = requests.get(base_url_fw + "/test_ratelimiting_1")
    assert res.status_code == 429
    # Fourth request :
    res = requests.get(base_url_fw + "/test_ratelimiting_1")
    assert res.status_code == 429

    time.sleep(5) # Wait until window expires
    
    # Fifth request :
    res = requests.get(base_url_fw + "/test_ratelimiting_1")
    assert res.status_code == 200
"""

"""
def test_set_ip_forwarded_for():
    # IP allowed :
    res = requests.get(base_url_fw + "/", headers={
        "X-Forwarded-For": "1.1.1.1"
    })
    assert res.status_code == 200
    # IP Geo-blocked :
    res = requests.get(base_url_fw + "/", headers={
        "X-Forwarded-For": "1.2.3.4"
    })
    assert res.status_code == 403
    assert res.text == "Your IP address is blocked due to geo restrictions (Your IP: 1.2.3.4)"
"""
