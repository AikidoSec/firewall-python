from utils import App, Request

django_mysql_gunicorn_app = App(8082)

django_mysql_gunicorn_app.add_payload(
    "test_sql_injection",
    safe_request=Request("/app/create/", data_type="form", body={"dog_name": "Bobby Tables"}),
    unsafe_request=Request("/app/create/", data_type="form", body={"dog_name": 'Dangerous bobby", 1); -- '}),
    test_event={
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {
            'dialect': 'mysql',
            'sql': 'INSERT INTO sample_app_dogs (dog_name, dog_boss) VALUES ("Dangerous bobby", 1); -- ", "N/A")'
        },
        'operation': 'MySQLdb.Cursor.execute',
        'pathToPayload': '.dog_name.[0]',
        'payload': '"Dangerous bobby\\", 1); -- "',
        'source': "body",
    }
)

django_mysql_gunicorn_app.test_all_payloads()
