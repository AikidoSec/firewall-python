import importlib.metadata
from unittest.mock import patch

import pytest

import aikido_zen

aikido_zen.protect()

import aikido_zen.sinks.builtins_import as builtins_import
from aikido_zen.background_process.packages import PackagesStore


@pytest.fixture(autouse=True)
def run_around_tests():
    PackagesStore.clear()
    builtins_import.names_without_version.clear()


def test_flask_import():
    import flask

    assert PackagesStore.get_package("flask")["version"] == "3.0.3"


def test_django_import():
    import django

    assert PackagesStore.get_package("django")["version"] == "4.0"


def test_name_without_a_distribution_is_looked_up_once():
    with patch(
        "importlib.metadata.version", wraps=importlib.metadata.version
    ) as version:
        for _ in range(10):
            import json

    assert [c.args for c in version.call_args_list] == [("json",)]
    assert PackagesStore.get_package("json") is None


def test_recursive_package_store(monkeypatch):
    """Test that recursive imports during package scanning don't cause max recursion depth errors."""

    def recursive_get_package(name):
        """Recursively add package and its dependencies to PackagesStore."""
        import flask

    PackagesStore.clear()
    monkeypatch.setattr(PackagesStore, "get_package", recursive_get_package)

    import flask

    # Restore the original method after the test
    monkeypatch.undo()


def test_recursive_package_store_2(monkeypatch):
    """Test that recursive imports during package scanning don't cause max recursion depth errors."""

    def recursive_add_package(name, version):
        """Recursively add package and its dependencies to PackagesStore."""
        if name == "django":
            import django

    PackagesStore.clear()
    monkeypatch.setattr(PackagesStore, "add_package", recursive_add_package)
    import django

    # Restore the original method after the test
    monkeypatch.undo()
