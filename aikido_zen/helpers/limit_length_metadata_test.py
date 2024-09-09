import pytest
from aikido_zen.helpers.limit_length_metadata import limit_length_metadata


def test_limit_length_metadata():
    # Test case 1: Check if values are truncated correctly
    metadata = {"key1": "value1", "key2": "value2longvalue", "key3": "value3"}
    max_length = 6
    expected_result = {"key1": "value1", "key2": "value2", "key3": "value3"}
    assert limit_length_metadata(metadata, max_length) == expected_result

    # Test case 2: Check if values are not truncated if within max length
    metadata = {"key1": "value1", "key2": "value2", "key3": "value3"}
    max_length = 10
    expected_result = {"key1": "value1", "key2": "value2", "key3": "value3"}
    assert limit_length_metadata(metadata, max_length) == expected_result

    metadata = {}
    max_length = 5
    expected_result = {}
    assert limit_length_metadata(metadata, max_length) == expected_result
