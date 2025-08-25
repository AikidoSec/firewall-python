from utils import App, Request

quart_postgres_uvicorn_app = App(8096)

quart_postgres_uvicorn_app.add_payload(
    "test_sql_injection",
    safe_request=Request("/create", data_type="form", body={"dog_name": "Bobby Tables"}),
    unsafe_request=Request("/create", data_type="form", body={"dog_name": "Dangerous Bobby', TRUE); -- "}),
    test_event={
        "blocked": True,
        "kind": "sql_injection",
        "metadata": {
            'dialect': "postgres",
            'sql': "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Dangerous Bobby', TRUE); -- ', FALSE)"
        },
        "operation": "asyncpg.connection.Connection.execute",
        "pathToPayload": ".dog_name",
        "payload": "\"Dangerous Bobby', TRUE); -- \"",
        "source": "body",
        "user_id": "user123"
    }
)

quart_postgres_uvicorn_app.test_all_payloads()
