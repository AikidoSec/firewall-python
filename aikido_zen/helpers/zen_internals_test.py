import ctypes

from aikido_zen.helpers import zen_internals

MYSQL = 8


def test_library_and_functions_are_loaded_when_module_is_imported():
    assert zen_internals._internals_lib is not None
    assert zen_internals._detect_sql_injection is not None
    assert zen_internals._detect_sql_injection.restype is ctypes.c_int


def test_detect_sql_injection_returns_library_result():
    query = b"select * from users where id = 1 or 1=1"

    assert zen_internals.detect_sql_injection(query, b"1 or 1=1", MYSQL) == 1
    assert zen_internals.detect_sql_injection(query, b"users", MYSQL) == 0


def test_detect_sql_injection_does_not_open_library_again(monkeypatch):
    def fail_to_open(_path):
        raise OSError("opened the library again")

    monkeypatch.setattr("aikido_zen.helpers.zen_internals.ctypes.CDLL", fail_to_open)

    query = b"select * from users where id = 1 or 1=1"
    assert zen_internals.detect_sql_injection(query, b"1 or 1=1", MYSQL) == 1


def test_detect_sql_injection_returns_error_when_function_is_not_loaded(monkeypatch):
    monkeypatch.setattr("aikido_zen.helpers.zen_internals._detect_sql_injection", None)

    query = b"select * from users where id = 1 or 1=1"
    assert zen_internals.detect_sql_injection(query, b"1 or 1=1", MYSQL) == 2


def test_load_returns_none_when_library_file_is_missing(monkeypatch, caplog):
    monkeypatch.setattr(
        "aikido_zen.helpers.zen_internals.get_binary_path",
        lambda: "/nonexistent/libzen_internals.so",
    )

    assert zen_internals._load() is None
    assert "Zen will NOT block SQL injection attacks" in caplog.text
    assert "Cannot find the zen-internals library" in caplog.text


def test_load_returns_none_when_library_fails_to_load(monkeypatch, caplog):
    monkeypatch.setattr(
        "aikido_zen.helpers.zen_internals.get_binary_path", lambda: __file__
    )

    assert zen_internals._load() is None
    assert "Zen will NOT block SQL injection attacks" in caplog.text
    assert "Failed to load the zen-internals library" in caplog.text


def test_bind_returns_none_when_library_is_not_loaded():
    assert zen_internals._bind(None, "detect_sql_injection", [], ctypes.c_int) is None


def test_bind_returns_none_when_function_is_missing():
    class LibraryWithoutFunctions:
        pass

    assert (
        zen_internals._bind(
            LibraryWithoutFunctions(), "detect_sql_injection", [], ctypes.c_int
        )
        is None
    )
