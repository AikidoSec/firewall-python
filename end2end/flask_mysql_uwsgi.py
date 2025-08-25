from utils import App, Request

flask_mysql_uwsgi_app = App(8088)

flask_mysql_uwsgi_app.add_payload(
    "test_sql_injection",
    safe_request=Request("/create", data_type="form", body={"dog_name": "Bobby Tables"}),
    unsafe_request=Request("/create", data_type="form", body={"dog_name": 'Dangerous bobby", 1); -- '}),
    test_event={
        "blocked": True,
        "kind": "sql_injection",
        'metadata': {
            'dialect': 'mysql',
            'sql': 'INSERT INTO dogs (dog_name, isAdmin) VALUES ("Dangerous bobby", 1); -- ", 0)',
        },
        'operation': 'MySQLdb.Cursor.execute',
        'pathToPayload': '.dog_name',
        'payload': '"Dangerous bobby\\", 1); -- "',
        'source': "body",
    }
)

flask_mysql_uwsgi_app.test_all_payloads()
