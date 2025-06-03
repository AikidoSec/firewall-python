import aikido_zen.sinks.clickhouse_driver
import pytest
from aikido_zen.background_process import reset_comms
from aikido_zen.context import Context
from aikido_zen.errors import AikidoSQLInjection


class Context1(Context):
    def __init__(self, body):
        self.cookies = {}
        self.headers = {}
        self.remote_address = "1.1.1.1"
        self.method = "POST"
        self.url = "url"
        self.query = {}
        self.body = body
        self.source = "express"
        self.route = "/"
        self.parsed_userinput = {}


@pytest.fixture(autouse=True)
def set_blocking_to_true(monkeypatch):
    monkeypatch.setenv("AIKIDO_BLOCK", "1")


@pytest.fixture
def client():
    from clickhouse_driver import Client

    return Client(
        host="127.0.0.1", port=9000, user="default", password="", database="default"
    )


def test_client_execute_without_context(client):
    reset_comms()
    dog_name = "Steve"
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    client.execute(sql)


def test_client_execute_safe(client):
    reset_comms()
    dog_name = "Steve"
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    Context1({"dog_name": dog_name}).set_as_current_context()
    client.execute(sql)


def test_client_execute_unsafe(client, monkeypatch):
    reset_comms()
    dog_name = "Malicious dog', 1); -- "
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    Context1({"dog_name": dog_name}).set_as_current_context()

    with pytest.raises(AikidoSQLInjection):
        client.execute(sql)

    monkeypatch.setenv("AIKIDO_BLOCK", "0")
    client.execute(sql)


def test_cursor_execute_safe():
    from clickhouse_driver import connect

    conn = connect("clickhouse://localhost:9000")
    reset_comms()
    dog_name = "Steve"
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    Context1({"dog_name": dog_name}).set_as_current_context()
    conn.cursor().execute(sql)


def test_cursor_execute_unsafe(monkeypatch):
    from clickhouse_driver import connect

    conn = connect("clickhouse://localhost:9000")
    reset_comms()
    dog_name = "Malicious dog', 1); -- "
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    Context1({"dog_name": dog_name}).set_as_current_context()

    with pytest.raises(AikidoSQLInjection):
        conn.cursor().execute(sql)

    monkeypatch.setenv("AIKIDO_BLOCK", "0")
    conn.cursor().execute(sql)


def test_client_execute_with_progress_safe(client):
    reset_comms()
    dog_name = "Steve"
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    Context1({"dog_name": dog_name}).set_as_current_context()
    client.execute_with_progress(sql)


def test_client_execute_with_progress_unsafe(client, monkeypatch):
    reset_comms()
    dog_name = "Malicious dog', 1); -- "
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    Context1({"dog_name": dog_name}).set_as_current_context()

    with pytest.raises(AikidoSQLInjection):
        client.execute_with_progress(sql)

    monkeypatch.setenv("AIKIDO_BLOCK", "0")
    client.execute_with_progress(sql)


def test_client_execute_iter_safe(client):
    reset_comms()
    dog_name = "Steve"
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    Context1({"dog_name": dog_name}).set_as_current_context()
    client.execute_iter(sql)


def test_client_execute_iter_unsafe(client, monkeypatch):
    reset_comms()
    dog_name = "Malicious dog', 1); -- "
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    Context1({"dog_name": dog_name}).set_as_current_context()

    with pytest.raises(AikidoSQLInjection):
        client.execute_iter(sql)

    monkeypatch.setenv("AIKIDO_BLOCK", "0")
    client.execute_iter(sql)
