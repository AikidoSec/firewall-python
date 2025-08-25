from utils import App, Request

flask_postgres_app = App(8090)

flask_postgres_app.add_payload(
    "test_sql_injection",
    safe_request=Request("/create", data_type="form", body={"dog_name": "Bobby Tables"}),
    unsafe_request=Request("/create", data_type="form", body={"dog_name": "Dangerous Bobby', TRUE); -- "}),
    test_event={
        "blocked": True,
        "kind": "sql_injection",
        "metadata": {
            "dialect": "postgres",
            "sql": "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Dangerous Bobby', TRUE); -- ', FALSE)"
        },
        "operation": "psycopg2.Connection.Cursor.execute",
        "pathToPayload": '.dog_name',
        "payload": '"Dangerous Bobby\', TRUE); -- "',
        "source": "body",
    }
)

flask_postgres_app.add_payload(
    "test_sql_injection_via_cookies",
    safe_request=Request("/create_with_cookie", "GET", headers={
        "Cookie": "dog_name=Safe Dog; ,2=2"
    }),
    unsafe_request=Request("/create_with_cookie", "GET", headers={
        "Cookie": "dog_name=Dangerous bobby', TRUE) --; ,2=2"
    }),
    test_event={
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {
            'dialect': "postgres",
            'sql': "INSERT INTO sample_app_Dogs (dog_name, is_admin) VALUES ('Dangerous bobby', TRUE) --', FALSE)"
        },
        'operation': "psycopg2.Connection.Cursor.execute",
        'pathToPayload': '.dog_name',
        'payload': "\"Dangerous bobby', TRUE) --\"",
        'source': "cookies",
    }
)

flask_postgres_app.test_all_payloads()
