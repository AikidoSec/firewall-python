import aikido_zen.sinks.clickhouse_driver
import pytest
from aikido_zen.background_process import reset_comms
from aikido_zen.context import Context
from aikido_zen.errors import AikidoSQLInjection

kind = "sql_injection"
op = "pymysql.connections.query"


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
