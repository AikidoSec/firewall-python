import ctypes
import os

import pytest

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


def test_load_returns_none_when_library_file_is_missing(monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.zen_internals._binary_path",
        lambda: "/nonexistent/libzen_internals.so",
    )

    internals_lib, error = zen_internals._load()
    assert internals_lib is None
    assert "Cannot find the zen-internals library" in error
    assert "Request support" in error


def test_load_returns_none_when_library_fails_to_load(monkeypatch):
    monkeypatch.setattr(
        "aikido_zen.helpers.zen_internals._binary_path", lambda: __file__
    )

    internals_lib, error = zen_internals._load()
    assert internals_lib is None
    assert "Failed to load the zen-internals library" in error


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


def test_warning_gives_the_load_error_when_library_is_missing(monkeypatch, caplog):
    monkeypatch.setattr(
        "aikido_zen.helpers.zen_internals._load_error",
        "Cannot find the zen-internals library for test-target.",
    )

    zen_internals._warn_unavailable(
        "Zen will NOT block SQL injection attacks", "detect_sql_injection"
    )

    assert (
        "Zen will NOT block SQL injection attacks. Cannot find the zen-internals "
        "library for test-target." in caplog.text
    )


def test_warning_names_the_missing_function_when_library_is_loaded(monkeypatch, caplog):
    monkeypatch.setattr("aikido_zen.helpers.zen_internals._load_error", None)

    zen_internals._warn_unavailable(
        "Zen will NOT block SQL injection attacks", "detect_sql_injection"
    )

    assert "Zen will NOT block SQL injection attacks." in caplog.text
    assert "has no detect_sql_injection function" in caplog.text


@pytest.mark.parametrize(
    "system, machine, host, file_name",
    [
        ("Darwin", "arm64", "", "libzen_internals_aarch64-apple-darwin.dylib"),
        ("Darwin", "x86_64", "", "libzen_internals_x86_64-apple-darwin.dylib"),
        (
            "Linux",
            "aarch64",
            "aarch64-unknown-linux-gnu",
            "libzen_internals_aarch64-unknown-linux-gnu.so",
        ),
        (
            "Linux",
            "x86_64",
            "x86_64-pc-linux-gnu",
            "libzen_internals_x86_64-unknown-linux-gnu.so",
        ),
        (
            "Linux",
            "aarch64",
            "aarch64-alpine-linux-musl",
            "libzen_internals_aarch64-unknown-linux-musl.so",
        ),
        (
            "Linux",
            "x86_64",
            "x86_64-pc-linux-musl",
            "libzen_internals_x86_64-unknown-linux-musl.so",
        ),
        ("Linux", "x86_64", None, "libzen_internals_x86_64-unknown-linux-gnu.so"),
        ("Windows", "AMD64", None, "libzen_internals_x86_64-pc-windows-gnu.dll"),
        ("Windows", "ARM64", None, "libzen_internals_aarch64-pc-windows-msvc.dll"),
    ],
)
def test_binary_path_picks_the_build_for_the_platform(
    monkeypatch, system, machine, host, file_name
):
    monkeypatch.setattr("platform.system", lambda: system)
    monkeypatch.setattr("platform.machine", lambda: machine)
    monkeypatch.setattr("sysconfig.get_config_var", lambda name: host)

    path = zen_internals._binary_path()

    assert os.path.basename(path) == file_name
    assert os.path.dirname(os.path.normpath(path)).endswith(
        os.path.join("aikido_zen", "libs")
    )


def test_binary_path_ignores_what_the_system_reports_about_libc(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.machine", lambda: "x86_64")
    monkeypatch.setattr("sysconfig.get_config_var", lambda name: "x86_64-pc-linux-gnu")
    monkeypatch.setattr("platform.libc_ver", lambda: ("", ""))
    monkeypatch.setattr("glob.glob", lambda pattern: ["/lib/ld-musl-x86_64.so.1"])

    assert os.path.basename(zen_internals._binary_path()) == (
        "libzen_internals_x86_64-unknown-linux-gnu.so"
    )


def test_binary_path_exists_for_this_machine():
    assert os.path.exists(zen_internals._binary_path())
