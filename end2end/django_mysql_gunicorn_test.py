from django_mysql.test_sql_attack import test_sql_attack
from utils.EventHandler import EventHandler
from utils.test_safe_vs_unsafe_payloads import test_safe_vs_unsafe_payloads

# e2e tests for django_mysql_gunicorn sample app
payloads_sql = {
    "safe": {"dog_name": "Bobby Tables"},
    "unsafe": {"dog_name": 'Dangerous bobby", 1); -- '},
    "json": False  # Form data
}
urls = {
    "enabled": "http://localhost:8082",
    "disabled": "http://localhost:8083"
}

event_handler = EventHandler()
event_handler.reset()
test_safe_vs_unsafe_payloads(payloads_sql, urls, route="/app/create")
print("✅ Tested safe/unsafe payloads on /app/create")

test_sql_attack(event_handler)
print("✅ Tested accurate reporting of an attack")

"""
def test_firewall_started_okay():
    events = fetch_events_from_mock("http://localhost:5000")
    started_events = filter_on_event_type(events, "started")
    assert len(started_events) == 1
    validate_started_event(started_events[0], ["gunicorn", "django"])
"""
