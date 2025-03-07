from __init__ import events
from utils import App, Request

flask_postgres_app = App(8090)

flask_postgres_app.add_payload(
    "sql", test_event=events["flask_postgres_attack_body"],
    safe_request=Request("/create", body={"dog_name": "Bobby Tables"}, data_type="form"),
    unsafe_request=Request("/create", body={"dog_name": "Dangerous Bobby', TRUE); -- "}, data_type="form")
)
flask_postgres_app.add_payload(
    "sql_cookie", test_event=["flask_postgres_attack_cookie"],
    safe_request=Request("/create_with_cookie", method="GET", cookies={"dog_name": "Bobby Tables"}),
    unsafe_request=Request("/create_with_cookie", method="GET", cookies={"dog_name": "Bobby', TRUE) -- "})
)

flask_postgres_app.test_all_payloads()
