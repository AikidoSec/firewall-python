import pytest
from .check_context_for_shell_injection import check_context_for_shell_injection
from aikido_firewall.context import Context


class Context1(Context):
    def __init__(self):
        self.cookies = {}
        self.headers = {}
        self.remote_address = "1.1.1.1"
        self.method = "POST"
        self.url = "url"
        self.query = {}
        self.body = {
            "domain": "www.example`whoami`.com",
        }
        self.source = "express"
        self.route = "/"
        self.parsed_userinput = {}


class Context2(Context):
    def __init__(self):
        self.cookies = {}
        self.headers = {}
        self.remote_address = "ip"
        self.method = "POST"
        self.url = "url"
        self.body = {}
        self.query = {
            "domain": "www.example`whoami`.com",
        }
        self.source = "express"
        self.route = "/"
        self.parsed_userinput = {}


def test_detect_shell_injection(monkeypatch):
    monkeypatch.setattr("aikido_firewall.context.get_current_context", lambda: None)

    context = Context1()
    result = check_context_for_shell_injection(
        command="binary --domain www.example`whoami`.com",
        operation="child_process.exec",
        context=context,
    )

    expected = {
        "operation": "child_process.exec",
        "kind": "shell_injection",
        "source": "body",
        "pathToPayload": ".domain",
        "metadata": {
            "command": "binary --domain www.example`whoami`.com",
        },
        "payload": "www.example`whoami`.com",
    }

    assert result == expected


def test_detect_shell_injection_from_route_params(monkeypatch):
    monkeypatch.setattr("aikido_firewall.context.get_current_context", lambda: None)

    context = Context2()
    result = check_context_for_shell_injection(
        command="binary --domain www.example`whoami`.com",
        operation="child_process.exec",
        context=context,
    )

    expected = {
        "operation": "child_process.exec",
        "kind": "shell_injection",
        "source": "query",
        "pathToPayload": ".domain",
        "metadata": {
            "command": "binary --domain www.example`whoami`.com",
        },
        "payload": "www.example`whoami`.com",
    }

    assert result == expected
