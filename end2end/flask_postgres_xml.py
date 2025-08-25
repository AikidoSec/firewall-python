from utils import App, Request

flask_postgres_xml_app = App(8092)

SQL_INJ_ATTACK_EVENT = {
    "blocked": True,
    "kind": "sql_injection",
    "metadata": {
        "dialect": "postgres",
        "sql": "INSERT INTO dogs (dog_name, isAdmin) VALUES ('Malicious dog', TRUE); -- ', FALSE)"
    },
    "operation": "psycopg2.Connection.Cursor.execute",
    "pathToPayload": ".dog_name.[0]",
    "payload": "\"Malicious dog', TRUE); -- \"",
    "source": "xml",
}

# Test both xml and lxml
flask_postgres_xml_app.add_payload(
    "test_xml_sql_inj",
    safe_request=Request("/xml_post", data_type="form", body='<dogs><dog dog_name="Bobby" /></dogs>'),
    unsafe_request=Request("/xml_post", data_type="form", body='<dogs><dog dog_name="Malicious dog\', TRUE); -- " /></dogs>'),
    test_event=SQL_INJ_ATTACK_EVENT
)
flask_postgres_xml_app.add_payload(
    "test_xml_sql_inj_(lxml)",
    safe_request=Request("/xml_post_lxml", data_type="form", body='<dogs><dog dog_name="Bobby" /></dogs>'),
    unsafe_request=Request("/xml_post_lxml", data_type="form", body='<dogs><dog dog_name="Malicious dog\', TRUE); -- " /></dogs>'),
    test_event=SQL_INJ_ATTACK_EVENT
)

flask_postgres_xml_app.test_all_payloads()
