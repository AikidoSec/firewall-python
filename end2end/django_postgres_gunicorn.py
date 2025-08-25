from utils import App, Request

django_postgres_gunicorn_app = App(8100)

django_postgres_gunicorn_app.add_payload(
    "test_sql_injection",
    safe_request=Request("/app/create", data_type="form", body={"dog_name": "Bobby Tables"}),
    unsafe_request=Request("/app/create", data_type="form", body={"dog_name": "Dangerous bobby', TRUE); -- "}),
    test_event={
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {
            'dialect': "postgres",
            'sql': "INSERT INTO sample_app_Dogs (dog_name, is_admin) VALUES ('Dangerous bobby', TRUE); -- ', FALSE)"
        },
        'operation': "psycopg2.Connection.Cursor.execute",
        'pathToPayload': '.dog_name.[0]',
        'payload': "\"Dangerous bobby', TRUE); -- \"",
        'source': "body",
    }
)

django_postgres_gunicorn_app.add_payload(
    "test_sql_injection_via_cookies",
    safe_request=Request("/app/create/via_cookies", "GET", headers={
        "Cookie": "dog_name=Safe Dog"
    }),
    unsafe_request=Request("/app/create/via_cookies", "GET", headers={
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

django_postgres_gunicorn_app.test_all_payloads()
