from aikido_zen.vulnerabilities.attack_wave.is_web_scan_path import (
    is_web_scan_path,
)
from aikido_zen.vulnerabilities.attack_wave.suspicious_paths import (
    suspicious_file_names,
    suspicious_directory_names,
)


def test_is_web_scan_path():
    assert is_web_scan_path("/.env")
    assert is_web_scan_path("/test/.env")
    assert is_web_scan_path("/test/.env.bak")
    assert is_web_scan_path("/.git/config")
    assert is_web_scan_path("/.aws/config")
    assert is_web_scan_path("/some/path/.git/test")
    assert is_web_scan_path("/some/path/.gitlab-ci.yml")
    assert is_web_scan_path("/some/path/.github/workflows/test.yml")
    assert is_web_scan_path("/.travis.yml")
    assert is_web_scan_path("/../example/")
    assert is_web_scan_path("/./test")
    assert is_web_scan_path("/Cargo.lock")
    assert is_web_scan_path("/System32/test")


def test_is_not_web_scan_path():
    assert not is_web_scan_path("/test/file.txt")
    assert not is_web_scan_path("/some/route/to/file.txt")
    assert not is_web_scan_path("/some/route/to/file.json")
    assert not is_web_scan_path("/en")
    assert not is_web_scan_path("/")
    assert not is_web_scan_path("/test/route")
    assert not is_web_scan_path("/static/file.css")
    assert not is_web_scan_path("/static/file.a461f56e.js")


def test_no_duplicates_in_file_names():
    unique_file_names = set(suspicious_file_names)
    assert len(unique_file_names) == len(suspicious_file_names), "File names should be unique"


def test_no_duplicates_in_directory_names():
    unique_directory_names = set(suspicious_directory_names)
    assert len(unique_directory_names) == len(
        suspicious_directory_names
    ), "Directory names should be unique"
