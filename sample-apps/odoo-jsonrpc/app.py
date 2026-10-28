import json
import sys

import aikido_zen

# The background process reimports this module. protect() starts that
# process, so it can only run in the server process, before psycopg2 loads.
if __name__ == "__main__":
    aikido_zen.protect()

import psycopg2


def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="db",
        user="user",
        password="password",
    )


class SQL:
    def __init__(self, code, *params):
        self.code = code
        self.params = params


class Cursor:
    def __init__(self, raw):
        self._obj = raw

    def execute(self, query, params=None):
        if isinstance(query, SQL):
            query, params = query.code, query.params
        self._obj.execute(query, params)

    def fetchone(self):
        return self._obj.fetchone()

    def close(self):
        self._obj.close()


def dog_name_from_call(payload):
    params = payload.get("params") or {}
    kwargs = params.get("kwargs") or {}
    if isinstance(kwargs, dict) and "dog_name" in kwargs:
        return kwargs["dog_name"]
    args = params.get("args") or []
    if args and isinstance(args[0], dict) and "dog_name" in args[0]:
        return args[0]["dog_name"]
    return None


def store_dog(dog_name, parameterized):
    conn = get_db_connection()
    cursor = Cursor(conn.cursor())
    try:
        if parameterized:
            cursor.execute(
                SQL(
                    "INSERT INTO dogs (dog_name, isAdmin) VALUES (%s, FALSE)",
                    dog_name,
                )
            )
        else:
            cursor.execute(
                "INSERT INTO dogs (dog_name, isAdmin) VALUES ('%s', FALSE)" % dog_name
            )
        conn.commit()
        cursor.execute("SELECT dog_name, isadmin FROM dogs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return {"dog_name": row[0], "isadmin": row[1]}
    finally:
        cursor.close()
        conn.close()


def respond(start_response, status, body, content_type):
    data = body.encode() if isinstance(body, str) else body
    start_response(
        status,
        [
            ("Content-Type", content_type),
            ("Content-Length", str(len(data))),
        ],
    )
    return [data]


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")
    if method == "GET" and path == "/":
        return respond(start_response, "200 OK", "ok", "text/plain")

    if method != "POST" or path not in (
        "/web/dataset/call_kw",
        "/jsonrpc",
        "/web/dataset/call_kw_safe",
    ):
        return respond(start_response, "404 Not Found", "not found", "text/plain")

    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    raw = environ["wsgi.input"].read(length) if length else b""
    try:
        payload = json.loads(raw.decode() or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return respond(start_response, "400 Bad Request", "invalid json", "text/plain")

    dog_name = dog_name_from_call(payload)
    if dog_name is None:
        return respond(
            start_response, "400 Bad Request", "missing dog_name", "text/plain"
        )

    try:
        stored = store_dog(dog_name, path == "/web/dataset/call_kw_safe")
    except Exception as exc:
        return respond(
            start_response, "500 Internal Server Error", str(exc), "text/plain"
        )
    return respond(start_response, "200 OK", json.dumps(stored), "application/json")


def main():
    from wsgiref.simple_server import make_server

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8120
    server = make_server("0.0.0.0", port, application)
    print(f"odoo-jsonrpc sample listening on {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
