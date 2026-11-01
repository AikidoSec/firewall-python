import functools
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import aikido_zen
from aikido_zen import protect
from aikido_zen.background_process.ipc import IPCClient
from aikido_zen.helpers.token import get_token_from_env


def test_protect_with_django(monkeypatch, caplog):
    protect()

    assert "starting" in caplog.text
    IPCClient.reset()
    assert IPCClient.get() == None


def test_protect_sets_token():
    aikido_zen.protect(token="MY_TOKEN_1")
    assert get_token_from_env().token == "MY_TOKEN_1"


def test_protect_does_not_start_without_gil(monkeypatch):
    monkeypatch.setattr("aikido_zen.gil_not_enabled", lambda: True)

    with patch("aikido_zen.check_socket_access") as check_socket_access, patch(
        "aikido_zen.start_background_process"
    ) as start_background_process:
        protect()

    check_socket_access.assert_not_called()
    start_background_process.assert_not_called()


class FakeLazyImports:
    def __init__(self, current_filter):
        self.current_filter = current_filter

    def get_lazy_imports_filter(self):
        return self.current_filter

    def set_lazy_imports_filter(self, func):
        self.current_filter = func


def use_fake_lazy_imports(monkeypatch, current_filter):
    lazy_imports = FakeLazyImports(current_filter)
    monkeypatch.setattr("aikido_zen.sys", lazy_imports)
    monkeypatch.setattr("aikido_zen._zen_lazy_imports_filter", None)
    return lazy_imports


def install_zen_lazy_imports_filter(monkeypatch, app_filter):
    lazy_imports = use_fake_lazy_imports(monkeypatch, app_filter)
    aikido_zen._keep_zen_imports_eager()
    return lazy_imports.current_filter


def test_zen_imports_stay_eager_and_others_go_to_the_app_filter(monkeypatch):
    asked = []

    def app_filter(importer, name, fromlist):
        asked.append(name)
        return name != "eager_in_app"

    zen_filter = install_zen_lazy_imports_filter(monkeypatch, app_filter)

    assert zen_filter("aikido_zen", "os", None) is False
    assert zen_filter("aikido_zen.sinks.os", "os", None) is False
    assert zen_filter("app", "json", None) is True
    assert zen_filter("app", "eager_in_app", None) is False
    assert zen_filter("aikido_zen_plugin", "json", None) is True
    assert zen_filter(None, "json", None) is True
    assert asked == ["json", "eager_in_app", "json", "json"]


def test_imports_stay_lazy_without_an_app_filter(monkeypatch):
    zen_filter = install_zen_lazy_imports_filter(monkeypatch, None)

    assert zen_filter("app", "json", None) is True
    assert zen_filter("aikido_zen.context", "json", None) is False


def test_zen_filter_is_installed_once(monkeypatch):
    lazy_imports = use_fake_lazy_imports(monkeypatch, None)

    aikido_zen._keep_zen_imports_eager()
    zen_filter = lazy_imports.current_filter
    aikido_zen._keep_zen_imports_eager()

    assert lazy_imports.current_filter is zen_filter


def test_zen_filter_is_installed_again_over_a_wrapper_of_it(monkeypatch):
    lazy_imports = use_fake_lazy_imports(monkeypatch, None)
    aikido_zen._keep_zen_imports_eager()

    @functools.wraps(lazy_imports.current_filter)
    def app_filter(importer, name, fromlist):
        return True

    lazy_imports.current_filter = app_filter
    aikido_zen._keep_zen_imports_eager()

    assert lazy_imports.current_filter("aikido_zen.sinks.os", "os", None) is False


def test_zen_filter_wraps_a_filter_the_app_set_later(monkeypatch):
    lazy_imports = use_fake_lazy_imports(monkeypatch, None)
    aikido_zen._keep_zen_imports_eager()

    lazy_imports.current_filter = lambda importer, name, fromlist: name != "eager"
    aikido_zen._keep_zen_imports_eager()
    zen_filter = lazy_imports.current_filter

    assert zen_filter("aikido_zen.sinks.os", "os", None) is False
    assert zen_filter("app", "eager", None) is False
    assert zen_filter("app", "json", None) is True


def test_no_filter_on_python_without_lazy_imports(monkeypatch):
    monkeypatch.setattr("aikido_zen.sys", SimpleNamespace())

    aikido_zen._keep_zen_imports_eager()


def attack_results_with_every_import_lazy(before_protect=""):
    script = (
        "import os\n"
        "os.environ['AIKIDO_BLOCK'] = 'true'\n"
        "import aikido_zen\n"
        f"{before_protect}"
        "aikido_zen.protect('daemon_disabled')\n"
        "import sqlite3\n"
        "from flask import Flask, request\n"
        "app = Flask(__name__)\n"
        "db = sqlite3.connect(':memory:', check_same_thread=False)\n"
        "@app.route('/')\n"
        "def index():\n"
        "    db.execute(\"SELECT '\" + request.args['name'] + \"'\")\n"
        "    return 'ok'\n"
        "@app.errorhandler(Exception)\n"
        "def error(e):\n"
        "    return type(e).__name__, 500\n"
        "client = app.test_client()\n"
        'print([client.get("/?name=x\' OR 1=1 --").get_data(as_text=True) for _ in range(3)])\n'
    )
    result = subprocess.run(
        [sys.executable, "-P", "-X", "lazy_imports=all", "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()[-1]


lazy_imports_only = pytest.mark.skipif(
    not hasattr(sys, "set_lazy_imports_filter"),
    reason="lazy imports were added in Python 3.15",
)


@lazy_imports_only
def test_zen_modules_load_eagerly_without_protect():
    script = (
        "import types\n"
        "import aikido_zen.background_process.routes as routes\n"
        "print(any(isinstance(v, types.LazyImportType) for v in vars(routes).values()))\n"
    )
    result = subprocess.run(
        [sys.executable, "-P", "-X", "lazy_imports=all", "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.splitlines()[-1] == "False"


@lazy_imports_only
def test_attacks_are_blocked_when_every_import_is_lazy():
    assert attack_results_with_every_import_lazy() == str(["AikidoSQLInjection"] * 3)


@lazy_imports_only
def test_attacks_are_blocked_when_the_app_replaces_the_filter_before_protect():
    replace_filter = (
        "aikido_zen.__name__\n"
        "import sys\n"
        "sys.set_lazy_imports_filter(lambda importer, name, fromlist: True)\n"
    )

    assert attack_results_with_every_import_lazy(replace_filter) == str(
        ["AikidoSQLInjection"] * 3
    )
