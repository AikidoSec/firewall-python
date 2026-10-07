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
    assert detect_path_traversal("/home/binaries/test", "/home/binaries") is True
    assert detect_path_traversal("/app/.env", "/app/.env") is True


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


def test_current_directory_references():
    """/./ should be normalized to /"""
    assert detect_path_traversal("/./etc/passwd", "/./etc") is True
    assert detect_path_traversal("/etc/./passwd", "/etc") is True
    assert detect_path_traversal("/etc/./passwd", "/etc/./") is True
    assert detect_path_traversal("/./etc/passwd", "/./etc/passwd") is True
    assert detect_path_traversal("/etc/./passwd", "/etc/./passwd") is True
    assert detect_path_traversal("/./etc/./passwd", "/./etc/./passwd") is True
    # Multiple /./ sequences
    assert detect_path_traversal("/././etc/passwd", "/././etc") is True
    assert detect_path_traversal("/etc/././passwd", "/etc/././passwd") is True


def test_path_normalization():
    """Paths with multiple slashes and /./ should be normalized and detected"""
    assert detect_path_traversal("//etc//passwd", "/etc") is True
    assert detect_path_traversal("/./etc/./passwd", "/etc") is True
    assert detect_path_traversal("/././etc/passwd", "/etc") is True
    # Paths without leading slash are not unsafe
    assert detect_path_traversal("etc/passwd", "etc") is False
    assert detect_path_traversal("", "") is False
    # Combined slashes and dot: ///.///etc/passwd should normalize to /etc/passwd
    assert detect_path_traversal("///.///etc/passwd", "///.///etc") is True
    assert detect_path_traversal("///.///etc/passwd", "///.///etc/passwd") is True


def test_replacement_char_prefix_does_not_hide_traversal():
    # Regression: AIKIDO-5RDTZW1V / AIKIDO-B3YABOSP — an attacker prepends
    # invalid UTF-8 bytes (\xff or surrogate sequences) to a traversal payload.
    # After decode("utf-8", errors="replace") both the stored body string and the
    # path_to_string() output start with the replacement character �, so the
    # user-input substring is still found in the file path and traversal is detected.
    replacement = "�"
    traversal = "/../../../../../etc/passwd"
    assert (
        detect_path_traversal(replacement + traversal, replacement + traversal) is True
    )
    # Three replacement chars (from \xed\xa0\x80, three separate bad bytes)
    assert (
        detect_path_traversal(replacement * 3 + traversal, replacement * 3 + traversal)
        is True
    )


def test_case_insensitive_path_containment():
    assert detect_path_traversal("/etc/passwd", "/ETC/passwd") is True
    assert detect_path_traversal("/etc/passwd", "/ETC/PASSWD") is True
    assert detect_path_traversal("/home/user/file.txt", "/HOME/USER/file.txt") is True
