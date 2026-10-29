import importlib.metadata
from unittest.mock import patch

import pytest

import aikido_zen

aikido_zen.protect()

from aikido_zen.background_process.packages import PackagesStore


@pytest.fixture(autouse=True)
def run_around_tests():
    PackagesStore.clear()
    PackagesStore.clear_names_without_version()


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

    calls = []

    def recursive_add_installed_package(name):
        """Recursively add package and its dependencies to PackagesStore."""
        calls.append(name)
        import flask

    PackagesStore.clear()
    monkeypatch.setattr(
        PackagesStore, "add_installed_package", recursive_add_installed_package
    )

    import flask

    # Restore the original method after the test
    monkeypatch.undo()
    assert calls == ["flask"]


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


def test_imports_during_scan_do_not_start_nested_scans():
    original_version = importlib.metadata.version

    def version_that_imports(name):
        import csv
        import email

        return original_version(name)

    with patch(
        "importlib.metadata.version", side_effect=version_that_imports
    ) as version:
        import json

    assert [c.args for c in version.call_args_list] == [("json",)]
