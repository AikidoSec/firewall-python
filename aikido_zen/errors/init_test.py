import gc
import weakref

import pytest

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
    assert str(exception) == "Zen has blocked unknown"


def test_aikido_sql_injection():
    exception = AikidoSQLInjection(dialect="MySQL")
    assert str(exception) == "Zen has blocked an SQL injection, dialect: MySQL"


def test_aikido_nosql_injection():
    exception = AikidoNoSQLInjection()
    assert str(exception) == "Zen has blocked a NoSQL injection"


def test_aikido_rate_limiting():
    exception = AikidoRateLimiting()
    assert str(exception) == "You are rate limited by Zen."


def test_aikido_shell_injection():
    exception = AikidoShellInjection()
    assert str(exception) == "Zen has blocked a shell injection"


def test_aikido_path_traversal():
    exception = AikidoPathTraversal()
    assert str(exception) == "Zen has blocked a path traversal attack"


def test_aikido_ssrf():
    exception = AikidoSSRF()
    assert str(exception) == "Zen has blocked a server-side request forgery"


def test_aikido_exception_custom_message():
    exception = AikidoException("Custom message")
    assert str(exception) == "Custom message"
    assert exception.args == ("Custom message",)


@pytest.mark.parametrize(
    "exception_type,args",
    [
        (AikidoException, ()),
        (AikidoException, ("Custom message",)),
        (AikidoSQLInjection, ("MySQL",)),
        (AikidoNoSQLInjection, ()),
        (AikidoRateLimiting, ()),
        (AikidoShellInjection, ()),
        (AikidoPathTraversal, ()),
        (AikidoSSRF, ()),
    ],
)
def test_aikido_exception_releases_caller_locals(exception_type, args):
    class Payload:
        pass

    def caller():
        payload = Payload()
        reference = weakref.ref(payload)
        try:
            raise exception_type(*args)
        except AikidoException:
            pass
        return reference

    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        reference = caller()
        assert reference() is None
    finally:
        if gc_was_enabled:
            gc.enable()
