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
        self.cached_ui_strings = {}


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
        self.cached_ui_strings = {}


def test_detect_shell_injection():
    context = Context1()
    context.set_as_current_context()
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


def test_detect_shell_injection_from_route_params():
    context = Context2()
    context.set_as_current_context()
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
