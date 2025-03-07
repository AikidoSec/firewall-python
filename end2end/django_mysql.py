from __init__ import events
from utils import App, Request

django_mysql_app = App(8080)

django_mysql_app.add_payload(
    "sql", test_event=events["django_mysql_attack_sql"],
    safe_request=Request(route="/app/create", body={'dog_name': 'Bobby'}, data_type="form"),
    unsafe_request= Request(route="/app/create", body={'dog_name': 'Dangerous bobby", 1); -- '}, data_type="form")
)
django_mysql_app.add_payload(
    "shell", test_event=events["django_mysql_attack_shell"],
    safe_request=Request(route="/app/shell/bobby", method="GET"),
    unsafe_request=Request(route="/app/shell/ls -la", method="GET")
)

django_mysql_app.test_all_payloads()
