from __init__ import events
from utils import App, Request

quart_postgres_app = App(8096)

quart_postgres_app.add_payload(
    "sql", test_event=events["quart_postgres_attack"],
    safe_request=Request(route="/create", body={'dog_name': 'Bobby'}, data_type="form"),
    unsafe_request= Request(route="/create", body={'dog_name': "Dangerous Bobby', TRUE); -- "}, data_type="form")
)

quart_postgres_app.test_all_payloads()
