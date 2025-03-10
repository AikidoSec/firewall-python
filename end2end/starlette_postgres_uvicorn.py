from __init__ import events
from utils import App, Request

starlette_postgres_app = App(8102, status_code_valid=201)

starlette_postgres_app.add_payload(
    "sql", test_event=events["quart_postgres_attack"],
    safe_request=Request(route="/create", body={'dog_name': 'Bobby'}, data_type="form"),
    unsafe_request=Request(route="/create", body={'dog_name': "Dangerous Bobby', TRUE); -- "}, data_type="form")
)

starlette_postgres_app.test_all_payloads()
starlette_postgres_app.test_rate_limiting()
starlette_postgres_app.test_blocking()
