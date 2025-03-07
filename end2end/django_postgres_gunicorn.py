from __init__ import events
from utils import App, Request

django_postgres_gunicorn_app = App(8100)

django_postgres_gunicorn_app.add_payload(
    "sql", test_event=events["django_postgres_attack"],
    safe_request=Request(route="/app/create", body={'dog_name': 'Bobby'}, data_type="form"),
    unsafe_request= Request(route="/app/create", body={'dog_name': "Dangerous bobby', TRUE); -- "}, data_type="form")
)

django_postgres_gunicorn_app.test_all_payloads()
