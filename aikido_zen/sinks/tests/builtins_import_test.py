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
