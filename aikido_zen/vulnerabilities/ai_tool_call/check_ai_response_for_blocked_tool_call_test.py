"""Unit tests for check_ai_response_for_blocked_tool_call"""

from types import SimpleNamespace

from aikido_zen.vulnerabilities.ai_tool_call.check_ai_response_for_blocked_tool_call import (
    check_ai_response_for_blocked_tool_call,
)


def _chat_completion_with_tool_call(name, arguments):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    tool_calls=[
                        SimpleNamespace(
                            function=SimpleNamespace(name=name, arguments=arguments)
                        )
                    ]
                )
            )
        ]
    )


def test_check_returns_attack_dict_when_blocked(monkeypatch):
    monkeypatch.setenv("AIKIDO_BLOCKED_AI_TOOL_NAMES", "read_file")
    monkeypatch.setenv("AIKIDO_BLOCKED_AI_TOOL_ARG_PATTERNS", "**/.env")

    result = check_ai_response_for_blocked_tool_call(
        _chat_completion_with_tool_call("read_file", '{"path": "config/.env"}'),
        operation="openai.Completions.create",
    )
    assert result["kind"] == "ai_tool_call"
    assert result["operation"] == "openai.Completions.create"
    assert result["metadata"]["tool"] == "read_file"
    assert result["metadata"]["pattern"] == "**/.env"
    assert result["payload"]["tool"] == "read_file"


def test_check_returns_empty_when_allowed(monkeypatch):
    monkeypatch.setenv("AIKIDO_BLOCKED_AI_TOOL_NAMES", "read_file")
    monkeypatch.setenv("AIKIDO_BLOCKED_AI_TOOL_ARG_PATTERNS", "**/.env")

    result = check_ai_response_for_blocked_tool_call(
        _chat_completion_with_tool_call("read_file", '{"path": "README.md"}'),
        operation="openai.Completions.create",
    )
    assert result == {}


def test_check_returns_empty_without_rules(monkeypatch):
    monkeypatch.delenv("AIKIDO_BLOCKED_AI_TOOL_NAMES", raising=False)
    monkeypatch.delenv("AIKIDO_BLOCKED_AI_TOOL_ARG_PATTERNS", raising=False)

    result = check_ai_response_for_blocked_tool_call(
        _chat_completion_with_tool_call("read_file", '{"path": "config/.env"}'),
        operation="openai.Completions.create",
    )
    assert result == {}
