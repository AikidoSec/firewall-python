import aikido_zen.sinks.clickhouse_driver
import pytest
from aikido_zen.background_process import reset_comms
from aikido_zen.errors import AikidoSQLInjection
import aikido_zen.test_utils as test_utils


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    reset_comms()
    monkeypatch.setenv("AIKIDO_BLOCK", "1")


@pytest.fixture
def client():
    from clickhouse_driver import Client

    return Client(
        host="127.0.0.1", port=9000, user="default", password="", database="default"
    )


def test_client_execute_without_context(client):
    dog_name = "Steve"
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    client.execute(sql)


def test_client_execute_safe(client):
    dog_name = "Steve"
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    test_utils.generate_and_set_context(value=dog_name)
    client.execute(sql)


def test_client_execute_unsafe(client, monkeypatch):
    dog_name = "Malicious dog', 1); -- "
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    test_utils.generate_and_set_context(value=dog_name)

    with pytest.raises(AikidoSQLInjection):
        client.execute(sql)

    monkeypatch.setenv("AIKIDO_BLOCK", "0")
    client.execute(sql)


def test_cursor_execute_safe():
    from clickhouse_driver import connect

    conn = connect("clickhouse://localhost:9000")
    dog_name = "Steve"
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    test_utils.generate_and_set_context(value=dog_name)
    conn.cursor().execute(sql)


def test_cursor_execute_unsafe(monkeypatch):
    from clickhouse_driver import connect

    conn = connect("clickhouse://localhost:9000")
    dog_name = "Malicious dog', 1); -- "
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    test_utils.generate_and_set_context(value=dog_name)

    with pytest.raises(AikidoSQLInjection):
        conn.cursor().execute(sql)

    monkeypatch.setenv("AIKIDO_BLOCK", "0")
    conn.cursor().execute(sql)


def test_client_execute_with_progress_safe(client):
    dog_name = "Steve"
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    test_utils.generate_and_set_context(value=dog_name)
    client.execute_with_progress(sql)


def test_client_execute_with_progress_unsafe(client, monkeypatch):
    dog_name = "Malicious dog', 1); -- "
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    test_utils.generate_and_set_context(value=dog_name)

    with pytest.raises(AikidoSQLInjection):
        client.execute_with_progress(sql)

    monkeypatch.setenv("AIKIDO_BLOCK", "0")
    client.execute_with_progress(sql)


def test_client_execute_iter_safe(client):
    dog_name = "Steve"
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    test_utils.generate_and_set_context(value=dog_name)
    client.execute_iter(sql)


def test_client_execute_iter_unsafe(client, monkeypatch):
    dog_name = "Malicious dog', 1); -- "
    sql = "INSERT INTO dogs (dog_name, isAdmin) VALUES ('{}' , 0)".format(dog_name)
    test_utils.generate_and_set_context(value=dog_name)

    with pytest.raises(AikidoSQLInjection):
        client.execute_iter(sql)

    monkeypatch.setenv("AIKIDO_BLOCK", "0")
    client.execute_iter(sql)
