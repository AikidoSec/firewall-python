import pytest
from .context_contains_sql_injection import context_contains_sql_injection
from aikido_zen.context import Context
from aikido_zen.helpers.headers import Headers
import aikido_zen.test_utils as test_utils


@pytest.mark.parametrize(
    "invalid_input",
    [
        None,
        123,  # Integer
        45.67,  # Float
        [],  # Empty list
        [1, 2, 3],  # List of integers
        {},  # Empty dictionary
        {"key": "value"},  # Dictionary
        set(),  # Empty set
        {1, 2, 3},  # Set of integers
        object(),  # Instance of a generic object
        lambda x: x,  # Lambda function
        (1, 2),  # Tuple
        b"bytes",  # Bytes
    ],
)
def test_doesnt_crash_with_invalid_sql(invalid_input):
    context = test_utils.generate_context(value=invalid_input)
    result = context_contains_sql_injection(
        sql=invalid_input,
        operation="mysqlclient.query",
        context=context,
        dialect="mysql",
    )
    assert result == {}


def _make_context_with_bytes_body(body_bytes):
    """Create a minimal context whose body comes from raw bytes (as a real request would)."""
    ctx = Context.__new__(Context)
    ctx.cookies = {}
    ctx.headers = Headers()
    ctx.remote_address = "1.2.3.4"
    ctx.method = "POST"
    ctx.url = "http://localhost:5000/user"
    ctx.query = {}
    ctx.source = "flask"
    ctx.route = "/user"
    ctx.subdomains = []
    ctx.parsed_userinput = {}
    ctx.xml = {}
    ctx.outgoing_req_redirects = []
    ctx.user = None
    ctx.rate_limit_group = None
    ctx.executed_middleware = False
    ctx.protection_forced_off = False
    ctx.route_params = []
    ctx.set_body(body_bytes)
    return ctx


def test_unicode_escape_sqli_bypass_via_bytes_body():
    # Regression: AIKIDO-FVRDOX5M — json.loads decodes # -> # so self.body has '#'
    # but the sink receives the raw decoded string with literal '#'.  Without
    # body_raw the firewall checks '#' against a query that has '#' and misses it.
    raw_payload = b'"\\' + b"u0023 ' Union Select password From users -- x\""
    ctx = _make_context_with_bytes_body(raw_payload)

    # body is the JSON-decoded form (with '#'); body_raw is the original decoded bytes string
    assert ctx.body.startswith("#")
    assert ctx.body_raw is not None
    assert "\\u0023" in ctx.body_raw

    # The SQL query the application builds using request.data.decode() (raw bytes → string)
    user_id_raw = ctx.body_raw  # what reaches the sink when app reads raw body
    sql = f"SELECT username FROM users WHERE id = '{user_id_raw}'"

    result = context_contains_sql_injection(
        sql=sql,
        operation="pymysql.execute",
        context=ctx,
        dialect="mysql",
    )
    assert result != {}, "SQLi via unicode-escape bypass should be detected"
    assert result["source"] == "body_raw"
