import ctypes
import os
import shutil
import subprocess
import sys

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


def test_load_returns_none_when_library_file_is_missing(monkeypatch, caplog):
    monkeypatch.setattr(
        "aikido_zen.helpers.zen_internals._binary_path",
        lambda: "/nonexistent/libzen_internals.so",
    )

    assert zen_internals._load() is None
    assert "Cannot find the zen-internals library" in caplog.text
    assert "Request support" in caplog.text


def test_load_returns_none_when_library_fails_to_load(monkeypatch, caplog):
    monkeypatch.setattr(
        "aikido_zen.helpers.zen_internals._binary_path", lambda: __file__
    )

    assert zen_internals._load() is None
    assert "Failed to load the zen-internals library" in caplog.text


def test_load_falls_back_to_the_musl_build_when_the_glibc_build_fails(
    monkeypatch, tmp_path
):
    gnu_path = tmp_path / "libzen_internals_x86_64-unknown-linux-gnu.so"
    gnu_path.write_text("not a library")
    shutil.copy(
        zen_internals._binary_path(), tmp_path / gnu_path.name.replace("-gnu", "-musl")
    )
    monkeypatch.setattr(
        "aikido_zen.helpers.zen_internals._binary_path", lambda: str(gnu_path)
    )

    assert zen_internals._load() is not None


def test_ip_matcher_round_trip():
    handle = zen_internals.ip_matcher_create([b"10.0.0.0/8", b"2001:db8::/32"])
    assert handle is not None
    assert zen_internals.ip_matcher_has(handle, b"10.1.2.3") is True
    assert zen_internals.ip_matcher_has(handle, b"2001:db8::1") is True
    assert zen_internals.ip_matcher_has(handle, b"8.8.8.8") is False
    zen_internals.ip_matcher_free(handle)


@pytest.mark.parametrize(
    "function", ["_ip_matcher_create", "_ip_matcher_has", "_ip_matcher_free"]
)
def test_ip_matcher_create_returns_none_when_function_is_not_loaded(
    monkeypatch, function
):
    monkeypatch.setattr(f"aikido_zen.helpers.zen_internals.{function}", None)

    assert zen_internals.has_ip_matcher() is False
    assert zen_internals.ip_matcher_create([b"10.0.0.0/8"]) is None


def test_bind_returns_none_when_library_is_not_loaded():
    assert zen_internals._bind(None, "detect_sql_injection", [], ctypes.c_int) is None


def test_bind_returns_none_when_function_is_missing(caplog):
    class LibraryWithoutFunctions:
        pass

    assert (
        zen_internals._bind(
            LibraryWithoutFunctions(), "detect_sql_injection", [], ctypes.c_int
        )
        is None
    )
    assert "has no detect_sql_injection function" in caplog.text


def _warnings_at_import(cdll_patch):
    script = (
        "import ctypes\n" f"{cdll_patch}\n" "import aikido_zen.helpers.zen_internals\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    return result.stdout + result.stderr


def test_warns_once_per_disabled_feature_when_library_fails_to_load():
    output = _warnings_at_import(
        "def fail(*args, **kwargs):\n"
        "    raise OSError('cannot open shared object file')\n"
        "ctypes.CDLL = fail"
    )

    assert "Failed to load the zen-internals library" in output
    assert "cannot open shared object file" in output
    assert "Zen will NOT block SQL injection attacks." in output
    assert "Zen will NOT apply IP lists or block SSRF attacks." in output


def test_warns_about_the_missing_function_when_library_is_loaded():
    output = _warnings_at_import(
        "real_cdll = ctypes.CDLL\n"
        "class WithoutSql:\n"
        "    def __init__(self, lib):\n"
        "        self._lib = lib\n"
        "    def __getattr__(self, name):\n"
        "        if name == 'detect_sql_injection':\n"
        "            raise AttributeError(name)\n"
        "        return getattr(self._lib, name)\n"
        "ctypes.CDLL = lambda path, *args, **kwargs: WithoutSql(real_cdll(path))"
    )

    assert "has no detect_sql_injection function" in output
    assert "Zen will NOT block SQL injection attacks." in output
    assert "Failed to load the zen-internals library" not in output


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
