import pytest
from .contains_unsafe_path_parts import contains_unsafe_path_parts


def test_safe_paths():
    assert not contains_unsafe_path_parts("/home/user/file.txt")
    assert not contains_unsafe_path_parts("C:\\Users\\User\\Documents\\file.txt")
    assert not contains_unsafe_path_parts("C:/Program Files/app.exe")


def test_dangerous_paths():
    assert contains_unsafe_path_parts("/home/user/../file.txt")
    assert contains_unsafe_path_parts("C:\\Users\\User\\..\\Documents\\file.txt")
    assert contains_unsafe_path_parts("..\\..\\file.txt")
    assert contains_unsafe_path_parts("../folder/file.txt")


def test_edge_cases():
    assert not contains_unsafe_path_parts("")
    assert not contains_unsafe_path_parts("..")
    assert not contains_unsafe_path_parts(".")
    assert contains_unsafe_path_parts("folder/../file.txt")
    assert contains_unsafe_path_parts("folder\\..\\file.txt")
