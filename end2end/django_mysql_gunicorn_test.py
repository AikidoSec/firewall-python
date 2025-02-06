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
test_safe_vs_unsafe_payloads(payloads_sql, urls, route="/app/create/")
print("✅ Tested safe/unsafe payloads on /app/create/")

test_sql_attack(
    event_handler,
    sql='INSERT INTO sample_app_dogs (dog_name, dog_boss) VALUES ("Dangerous bobby", 1); -- ", "N/A")',
    sink="MySQLdb.Cursor.execute"
)
print("✅ Tested accurate reporting of an attack")
