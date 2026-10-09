"""Unit tests for detect_blocked_ai_tool_call"""

import pytest

from aikido_zen.vulnerabilities.ai_tool_call.detect_blocked_ai_tool_call import (
    argument_matches_pattern,
    detect_blocked_ai_tool_call,
)


@pytest.mark.parametrize(
    "arguments,pattern,expected",
    [
        ('{"path": "config/.env"}', "**/.env", True),
        ('{"path": "/var/app/.env"}', "**/.env", True),
        ('{"path": "README.md"}', "**/.env", False),
        ({"path": "secrets/.env"}, "**/.env", True),
        ('{"file": "data.txt"}', "**/.env", False),
    ],
)
def test_argument_matches_pattern(arguments, pattern, expected):
    assert argument_matches_pattern(arguments, pattern) is expected


def test_blocked_when_name_only_rule():
    assert (
        detect_blocked_ai_tool_call(
            "read_file",
            '{"path": "README.md"}',
            names={"read_file", "write_file", "shell"},
            patterns=[],
        )
        is True
    )


def test_blocked_when_name_and_pattern_match():
    assert (
        detect_blocked_ai_tool_call(
            "read_file",
            '{"path": "app/.env"}',
            names={"read_file"},
            patterns=["**/.env"],
        )
        is True
    )


def test_allowed_when_name_matches_but_path_safe():
    assert (
        detect_blocked_ai_tool_call(
            "read_file",
            '{"path": "README.md"}',
            names={"read_file"},
            patterns=["**/.env"],
        )
        is False
    )


def test_allowed_when_different_tool_name():
    assert (
        detect_blocked_ai_tool_call(
            "list_files",
            '{"path": ".env"}',
            names={"read_file"},
            patterns=["**/.env"],
        )
        is False
    )


def test_allowed_for_safe_internal_tool():
    assert (
        detect_blocked_ai_tool_call(
            "get_order",
            '{"order_id": "ORD-42"}',
            names={"read_file", "write_file", "shell"},
            patterns=[],
        )
        is False
    )
