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
        == "(AikidoException(...), 'Aikido Zen has blocked unknown')"
    )


def test_aikido_sql_injection():
    exception = AikidoSQLInjection(dialect="MySQL")
    assert (
        str(exception)
        == "(AikidoSQLInjection(...), 'Aikido Zen has blocked an SQL injection, dialect: MySQL')"
    )


def test_aikido_nosql_injection():
    exception = AikidoNoSQLInjection()
    assert (
        str(exception)
        == "(AikidoNoSQLInjection(...), 'Aikido Zen has blocked a NoSQL injection')"
    )


def test_aikido_rate_limiting():
    exception = AikidoRateLimiting()
    assert (
        str(exception)
        == "(AikidoRateLimiting(...), 'You are rate limited by Aikido Zen.')"
    )


def test_aikido_shell_injection():
    exception = AikidoShellInjection()
    assert (
        str(exception)
        == "(AikidoShellInjection(...), 'Aikido Zen has blocked a shell injection')"
    )


def test_aikido_path_traversal():
    exception = AikidoPathTraversal()
    assert (
        str(exception)
        == "(AikidoPathTraversal(...), 'Aikido Zen has blocked a path traversal attack')"
    )


def test_aikido_ssrf():
    exception = AikidoSSRF()
    assert (
        str(exception)
        == "(AikidoSSRF(...), 'Aikido Zen has blocked a server-side request forgery')"
    )
