import pytest
from .unsafe_path_start import starts_with_unsafe_path


def test_linux_root_paths():
    assert starts_with_unsafe_path("/etc/passwd", "/etc")
    assert starts_with_unsafe_path("/bin/bash", "/bin")
    assert starts_with_unsafe_path("/lib/modules", "/lib")
    assert starts_with_unsafe_path("/home/user/file.txt", "/home")
    assert starts_with_unsafe_path("/usr/local/bin", "/usr")
    assert starts_with_unsafe_path("/var/log/syslog", "/var")


def test_windows_paths():
    assert starts_with_unsafe_path("c:/Program Files/app.exe", "c:/")
    assert starts_with_unsafe_path("c:\\Windows\\System32\\cmd.exe", "c:\\")
    assert not starts_with_unsafe_path("d:/Documents/file.txt", "c:/")


def test_edge_cases():
    assert not starts_with_unsafe_path("", "/etc")
    assert not starts_with_unsafe_path("/etc", "")
    assert starts_with_unsafe_path("c:/", "c:/")
    assert starts_with_unsafe_path("c:/folder/file.txt", "c:/folder")
