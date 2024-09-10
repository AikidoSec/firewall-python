import pytest
from .detect_path_traversal import detect_path_traversal


def test_empty_user_input():
    assert detect_path_traversal("test.txt", "") is False


def test_empty_file_input():
    assert detect_path_traversal("", "test") is False


def test_empty_user_input_and_file_input():
    assert detect_path_traversal("", "") is False


def test_user_input_is_a_single_character():
    assert detect_path_traversal("test.txt", "t") is False


def test_file_input_is_a_single_character():
    assert detect_path_traversal("t", "test") is False


def test_same_as_user_input():
    assert detect_path_traversal("text.txt", "text.txt") is False


def test_with_directory_before():
    assert detect_path_traversal("directory/text.txt", "text.txt") is False


def test_with_both_directory_before():
    assert detect_path_traversal("directory/text.txt", "directory/text.txt") is False


def test_user_input_and_file_input_are_single_characters():
    assert detect_path_traversal("t", "t") is False


def test_it_flags_dot_dot_slash():
    assert detect_path_traversal("../test.txt", "../") is True


def test_it_flags_backslash_dot_dot():
    assert detect_path_traversal("..\\test.txt", "..\\") is True


def test_it_flags_double_dot_slash():
    assert detect_path_traversal("../../test.txt", "../../") is True


def test_it_flags_double_dot_backslash():
    assert detect_path_traversal("..\\..\\test.txt", "..\\..\\") is True


def test_it_flags_four_dot_slash():
    assert detect_path_traversal("../../../../test.txt", "../../../../") is True


def test_it_flags_three_dot_backslash():
    assert detect_path_traversal("..\\..\\..\\test.txt", "..\\..\\..\\") is True


def test_user_input_is_longer_than_file_path():
    assert detect_path_traversal("../file.txt", "../../file.txt") is False


def test_absolute_linux_path():
    assert detect_path_traversal("/etc/passwd", "/etc/passwd") is True


def test_linux_user_directory():
    assert detect_path_traversal("/home/user/file.txt", "/home/user/") is True


def test_windows_drive_letter():
    assert detect_path_traversal("C:\\file.txt", "C:\\") is True


def test_no_path_traversal():
    assert (
        detect_path_traversal("/appdata/storage/file.txt", "/storage/file.txt") is False
    )


def test_does_not_flag_test():
    assert detect_path_traversal("/app/test.txt", "test") is False


def test_does_not_flag_example_test_txt():
    assert (
        detect_path_traversal("/app/data/example/test.txt", "example/test.txt") is False
    )


def test_does_not_absolute_path_with_different_folder():
    assert detect_path_traversal("/etc/app/config", "/etc/hack/config") is False


def test_does_not_absolute_path_inside_another_folder():
    assert detect_path_traversal("/etc/app/data/etc/config", "/etc/config") is False


def test_disable_checkPathStart():
    assert detect_path_traversal("/etc/passwd", "/etc/passwd", False) is False
