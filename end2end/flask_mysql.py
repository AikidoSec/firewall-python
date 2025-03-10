from __init__ import events
from utils import App, Request

flask_mysql_app = App(8086)

flask_mysql_app.add_payload(
    "sql", test_event=events["flask_mysql_attack_sql"],
    safe_request=Request("/create", body={"dog_name": "Bobby"}, data_type="form"),
    unsafe_request=Request("/create", body={"dog_name": "Dangerous bobby\", 1); -- "}, data_type="form")
)
flask_mysql_app.add_payload(
    "shell", test_event=events["flask_mysql_attack_shell"],
    safe_request=Request(route="/shell/bobby", method="GET"),
    unsafe_request=Request(route="/shell/ls -la", method="GET", headers={"user": "456"})
)

flask_mysql_app.test_all_payloads()
flask_mysql_app.test_rate_limiting()
