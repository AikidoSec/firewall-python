import pytest

import aikido_zen

aikido_zen.protect()

from aikido_zen.background_process.packages import PackagesStore


@pytest.fixture(autouse=True)
def run_around_tests():
    PackagesStore.clear()


def test_flask_import():
    import flask

    assert PackagesStore.get_package("flask")["version"] == "3.0.3"


def test_django_import():
    import django

    assert PackagesStore.get_package("django")["version"] == "4.0"


def recursive_get_package(name):
    """Recursively add package and its dependencies to PackagesStore."""
    import flask


def test_recursive_package_store(monkeypatch):
      """Test that recursive imports during package scanning don't cause max recursion depth errors."""
    PackagesStore.clear()
    monkeypatch.setattr(PackagesStore, "get_package", recursive_get_package)

    import flask

    # Restore the original method after the test
    monkeypatch.undo()


def recursive_add_package(name, version):
    """Recursively add package and its dependencies to PackagesStore."""
    if name == "django":
        import django


def test_recursive_package_store_2(monkeypatch):
    PackagesStore.clear()
    monkeypatch.setattr(PackagesStore, "add_package", recursive_add_package)
    import django

    # Restore the original method after the test
    monkeypatch.undo()
