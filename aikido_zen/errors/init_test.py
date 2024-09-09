from . import (
    AikidoException,
    AikidoSQLInjection,
    AikidoNoSQLInjection,
    AikidoRateLimiting,
    AikidoShellInjection,
    AikidoPathTraversal,
    AikidoSSRF,
)


def test_aikido_exception_default_message():
    exception = AikidoException()
    assert (
        str(exception)
        == "(AikidoException(...), 'Aikido firewall has blocked unknown')"
    )


def test_aikido_sql_injection():
    exception = AikidoSQLInjection(dialect="MySQL")
    assert (
        str(exception)
        == "(AikidoSQLInjection(...), 'Aikido firewall has blocked an SQL injection, dialect: MySQL')"
    )


def test_aikido_nosql_injection():
    exception = AikidoNoSQLInjection()
    assert (
        str(exception)
        == "(AikidoNoSQLInjection(...), 'Aikido firewall has blocked a NoSQL injection')"
    )


def test_aikido_rate_limiting():
    exception = AikidoRateLimiting()
    assert (
        str(exception)
        == "(AikidoRateLimiting(...), 'You are rate limited by Aikido firewall.')"
    )


def test_aikido_shell_injection():
    exception = AikidoShellInjection()
    assert (
        str(exception)
        == "(AikidoShellInjection(...), 'Aikido firewall has blocked a shell injection')"
    )


def test_aikido_path_traversal():
    exception = AikidoPathTraversal()
    assert (
        str(exception)
        == "(AikidoPathTraversal(...), 'Aikido firewall has blocked a path traversal attack')"
    )


def test_aikido_ssrf():
    exception = AikidoSSRF()
    assert (
        str(exception)
        == "(AikidoSSRF(...), 'Aikido firewall has blocked a server-side request forgery')"
    )