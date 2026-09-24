"""Unit tests for extract_tool_calls_from_ai_response"""

from types import SimpleNamespace

from aikido_zen.vulnerabilities.ai_tool_call.extract_tool_calls_from_ai_response import (
    extract_tool_calls_from_ai_response,
)


def test_extract_tool_calls_from_chat_completions():
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    tool_calls=[
                        SimpleNamespace(
                            function=SimpleNamespace(
                                name="read_file",
                                arguments='{"path": "config/.env"}',
                            )
                        )
                    ]
                )
            )
        ]
    )
    assert extract_tool_calls_from_ai_response(response) == [
        ("read_file", '{"path": "config/.env"}')
    ]


def test_extract_tool_calls_from_responses_api():
    response = SimpleNamespace(
        output=[
            SimpleNamespace(
                type="function_call",
                name="read_file",
                arguments='{"path": "/app/.env"}',
            )
        ]
    )
    assert extract_tool_calls_from_ai_response(response) == [
        ("read_file", '{"path": "/app/.env"}')
    ]
