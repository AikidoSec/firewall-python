from aikido_zen.vulnerabilities.attack_wave_detection.is_web_scan_path import (
    is_web_scan_path,
)
from aikido_zen.vulnerabilities.attack_wave_detection.paths import (
    file_names,
    directory_names,
)


def test_is_web_scan_path():
    assert is_web_scan_path("/.env", 404)
    assert is_web_scan_path("/test/.env", 404)
    assert is_web_scan_path("/test/.env.bak", 404)
    assert is_web_scan_path("/.git/config", 404)
    assert is_web_scan_path("/.aws/config", 404)
    assert is_web_scan_path("/some/path/.git/test", 404)
    assert is_web_scan_path("/some/path/.gitlab-ci.yml", 404)
    assert is_web_scan_path("/some/path/.github/workflows/test.yml", 404)
    assert is_web_scan_path("/.travis.yml", 404)
    assert is_web_scan_path("/../example/", 404)
    assert is_web_scan_path("/./test", 404)
    assert is_web_scan_path("/Cargo.lock", 404)
    assert is_web_scan_path("/System32/test", 404)


def test_is_not_web_scan_path():
    assert not is_web_scan_path("/test/file.txt", 404)
    assert not is_web_scan_path("/some/route/to/file.txt", 404)
    assert not is_web_scan_path("/some/route/to/file.json", 404)
    assert not is_web_scan_path("/en", 404)
    assert not is_web_scan_path("/", 404)
    assert not is_web_scan_path("/test/route", 404)
    assert not is_web_scan_path("/static/file.css", 404)
    assert not is_web_scan_path("/static/file.a461f56e.js", 404)


def test_foreign_extensions_404():
    assert is_web_scan_path("/admin.php", 404)
    assert is_web_scan_path("/app.jsp", 404)


def test_foreign_extensions_non_404():
    assert not is_web_scan_path("/admin.php", 200)
    assert not is_web_scan_path("/admin.php", 301)
    assert not is_web_scan_path("/app.jsp", 200)


def test_no_duplicates_in_file_names():
    unique_file_names = set(file_names)
    assert len(unique_file_names) == len(file_names), "File names should be unique"


def test_no_duplicates_in_directory_names():
    unique_directory_names = set(directory_names)
    assert len(unique_directory_names) == len(
        directory_names
    ), "Directory names should be unique"
