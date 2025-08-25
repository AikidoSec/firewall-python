from end2end.utils import assert_eq
from utils import App, Request

django_mysql_app = App(8080)

django_mysql_app.add_payload(
    "test_sql_injection",
    safe_request=Request("/app/create", data_type="form", body={"dog_name": "Bobby Tables"}),
    unsafe_request=Request("/app/create", data_type="form", body={"dog_name": 'Dangerous bobby", 1); -- '}),
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

django_mysql_app.add_payload(
    "test_shell_injection",
    safe_request=None,  # Don't test safeness
    unsafe_request=Request("/app/shell/ls -la", "GET"),
    test_event={
        "blocked": True,
        "kind": "shell_injection",
        'metadata': {'command': 'ls -la'},
        'operation': 'subprocess.Popen',
        'pathToPayload': '.[0]',
        'payload': '"ls -la"',
        'source': "route_params",
    }
)


def test_heartbeat(app):
    heartbeat = app.get_heartbeat()
    route1 = heartbeat["routes"][0]
    stats = heartbeat["stats"]
    packages = set(map(lambda x: x["name"], heartbeat["packages"]))

    # Validate routes
    assert_eq(route1["path"], "/app/create")
    assert_eq(route1["method"], "POST")
    assert_eq(route1["hits"], 1)

    assert_eq(route1["apispec"]["body"]["type"], "form-urlencoded")
    assert_eq(route1["apispec"]["body"]["schema"], {
        'type': 'object',
        'properties': {
            'dog_name': {
                'items': {'type': 'string'},
                'type': 'array'
            }
        }
    })
    assert_eq(route1["apispec"]["body"]["query"], None)
    assert_eq(route1["apispec"]["body"]["auth"], None)

    # Validate stats
    assert_eq(stats["requests"]["attacksDetected"]["blocked"], 2)
    assert_eq(stats["requests"]["attacksDetected"]["total"], 2)
    assert_eq(stats["requests"]["total"], 3)

    # Validate packages
    assert_eq(packages, {'wrapt', 'asgiref', 'aikido_zen', 'django', 'sqlparse', 'regex', 'mysqlclient'})


django_mysql_app.test_all_payloads()
test_heartbeat(django_mysql_app)
