import pytest
from aikido_zen.helpers.is_useful_route import is_useful_route


def test_not_found_or_method_not_allowed():
    assert is_useful_route(status_code=404, route="/", method="GET") is False
    assert is_useful_route(status_code=405, route="/", method="GET") is False


def test_discover_route_for_all_other_status_codes():
    assert is_useful_route(status_code=200, route="/", method="GET") is True
    assert is_useful_route(status_code=500, route="/", method="GET") is False
    assert is_useful_route(status_code=400, route="/", method="GET") is False
    assert is_useful_route(status_code=199, route="/", method="GET") is False
    assert is_useful_route(status_code=399, route="/", method="GET") is True
    assert is_useful_route(status_code=300, route="/", method="GET") is True
    assert is_useful_route(status_code=201, route="/", method="GET") is True


def test_not_discover_route_for_excluded_methods():
    assert is_useful_route(status_code=200, route="/", method="OPTIONS") is False
    assert is_useful_route(status_code=200, route="/", method="HEAD") is False


def test_not_discover_route_for_excluded_methods_with_other_status_codes():
    assert is_useful_route(status_code=404, route="/", method="OPTIONS") is False
    assert is_useful_route(status_code=405, route="/", method="HEAD") is False


def test_not_discover_static_files():
    assert (
        is_useful_route(status_code=200, route="/service-worker.js", method="GET")
        is False
    )
    assert (
        is_useful_route(
            status_code=200,
            route="/precache-manifest.10faec0bee24db502c8498078126dd53.js",
            method="POST",
        )
        is False
    )
    assert (
        is_useful_route(
            status_code=200, route="/img/icons/favicon-16x16.png", method="GET"
        )
        is False
    )
    assert (
        is_useful_route(status_code=200, route="/fonts/icomoon.ttf", method="GET")
        is False
    )


def test_allow_html_files():
    assert is_useful_route(status_code=200, route="/index.html", method="GET") is False
    assert (
        is_useful_route(status_code=200, route="/contact.html", method="GET") is False
    )


def test_allow_files_with_one_character_extension():
    assert is_useful_route(status_code=200, route="/a.a", method="GET") is True


def test_allow_files_with_six_or_more_character_extensions():
    assert is_useful_route(status_code=200, route="/a.aaaaaa", method="GET") is True
    assert is_useful_route(status_code=200, route="/a.aaaaaaa", method="GET") is True


def test_ignore_files_that_end_with_properties():
    assert (
        is_useful_route(status_code=200, route="/file.properties", method="GET")
        is False
    )
    assert (
        is_useful_route(
            status_code=200, route="/directory/file.properties", method="GET"
        )
        is False
    )


def test_ignore_files_or_directories_that_start_with_dot():
    assert is_useful_route(status_code=200, route="/.env", method="GET") is False
    assert (
        is_useful_route(status_code=200, route="/.aws/credentials", method="GET")
        is False
    )
    assert (
        is_useful_route(status_code=200, route="/directory/.gitconfig", method="GET")
        is False
    )
    assert (
        is_useful_route(status_code=200, route="/hello/.gitignore/file", method="GET")
        is False
    )


def test_ignore_files_that_end_with_php():
    assert is_useful_route(status_code=200, route="/file.php", method="GET") is False
    assert (
        is_useful_route(
            status_code=200, route="/app_dev.php/_profiler/phpinfo", method="GET"
        )
        is False
    )


def test_allow_well_known_directory():
    assert is_useful_route(status_code=200, route="/.well-known", method="GET") is False
    assert (
        is_useful_route(
            status_code=200, route="/.well-known/change-password", method="GET"
        )
        is True
    )
    assert (
        is_useful_route(
            status_code=200, route="/.well-known/security.txt", method="GET"
        )
        is False
    )


def test_ignore_certain_strings():
    assert (
        is_useful_route(
            status_code=200, route="/cgi-bin/luci/;stok=/locale", method="GET"
        )
        is False
    )
    assert (
        is_useful_route(status_code=200, route="/whatever/cgi-bin", method="GET")
        is False
    )


def test_ignore_fonts():
    assert (
        is_useful_route(status_code=200, route="/fonts/icomoon.ttf", method="GET")
        is False
    )
    assert (
        is_useful_route(status_code=200, route="/fonts/icomoon.woff", method="GET")
        is False
    )
    assert (
        is_useful_route(status_code=200, route="/fonts/icomoon.woff2", method="GET")
        is False
    )


def test_ignore_files_that_end_with_config():
    assert (
        is_useful_route(
            status_code=200,
            route="/blog/App_Config/ConnectionStrings.config",
            method="GET",
        )
        is False
    )


def test_allow_redirects():
    assert is_useful_route(status_code=301, route="/", method="GET") is True
    assert is_useful_route(status_code=302, route="/", method="GET") is True
    assert is_useful_route(status_code=303, route="/", method="GET") is True
    assert is_useful_route(status_code=307, route="/", method="GET") is True
    assert is_useful_route(status_code=308, route="/", method="GET") is True
