import pytest
from aikido_zen.helpers.build_path_to_payload import build_path_to_payload


def test_build_path_to_payload_empty():
    assert build_path_to_payload([]) == "."


def test_build_path_to_payload_single_object():
    path = [{"type": "object", "key": "name"}]
    assert build_path_to_payload(path) == ".name"


def test_build_path_to_payload_single_array():
    path = [{"type": "array", "index": 0}]
    assert build_path_to_payload(path) == ".[0]"


def test_build_path_to_payload_single_jwt():
    path = [{"type": "jwt"}]
    assert build_path_to_payload(path) == "<jwt>"


def test_build_path_to_payload_mixed_types():
    path = [
        {"type": "object", "key": "user"},
        {"type": "array", "index": 2},
        {"type": "jwt"},
        {"type": "object", "key": "details"},
        {"type": "array", "index": 1},
    ]
    assert build_path_to_payload(path) == ".user.[2]<jwt>.details.[1]"


def test_build_path_to_payload_multiple_objects():
    path = [
        {"type": "object", "key": "user"},
        {"type": "object", "key": "details"},
        {"type": "object", "key": "address"},
    ]
    assert build_path_to_payload(path) == ".user.details.address"
