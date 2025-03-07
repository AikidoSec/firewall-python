from __init__ import events
from utils import App, Request

flask_mysql_uwsgi_app = App(8088)

flask_mysql_uwsgi_app.add_payload(
    "sql", test_event=events["flask_mysql_attack"],
    safe_request=Request(route="/create", body={'dog_name': 'Bobby'}, data_type="form"),
    unsafe_request=Request(route="/create", body={'dog_name': 'Dangerous bobby", 1); -- '}, data_type="form")
)

flask_mysql_uwsgi_app.test_all_payloads()
