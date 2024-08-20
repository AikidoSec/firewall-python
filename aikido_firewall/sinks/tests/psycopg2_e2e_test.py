import pytest
from aikido_firewall.vulnerabilities.sql_injection.dialects import Postgres


@pytest.fixture
def mock_get_comms(mocker):
    """Fixture to mock the get_comms function."""

    class FakeComms:
        def __init__(self):
            self.action = None
            self.obj = None
            self.receive = False

        def send_data_to_bg_process(self, action, obj, receive):
            self.action = action
            self.obj = obj
            self.receive = receive
            return {"success": True, "data": True}

    return FakeComms


def test_execute_method(mock_get_comms, mocker):
    mock_vuln_scan = mocker.patch(
        "aikido_firewall.vulnerabilities.run_vulnerability_scan"
    )
    mock_vuln_scan.side_effect = Exception("Scan failed")

    mock_class = mock_get_comms()
    mocker.patch(
        "aikido_firewall.background_process.comms.get_comms", return_value=mock_class
    )

    import aikido_firewall.sinks.psycopg2

    with pytest.raises(Exception, match="Scan failed"):
        import psycopg2

        conn = psycopg2.connect(
            host="localhost", database="db", user="user", password="password"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dogs")
        dogs = cursor.fetchall()

    call_args = mock_vuln_scan.call_args_list[0][
        1
    ]  #  # Get the first call's positional arguments
    assert call_args["kind"] == "sql_injection"
    assert call_args["op"] == "pymysql.connection.cursor.execute"
    assert call_args["args"][0] == "SELECT * FROM dogs"
    assert isinstance(call_args["args"][1], Postgres)
