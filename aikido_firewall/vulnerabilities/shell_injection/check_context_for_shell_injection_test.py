import pytest
from .check_context_for_shell_injection import check_context_for_shell_injection


class Context1:
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


class Context2:
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


def test_detect_shell_injection():
    result = check_context_for_shell_injection(
        command="binary --domain www.example`whoami`.com",
        operation="child_process.exec",
        context=Context1(),
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
    result = check_context_for_shell_injection(
        command="binary --domain www.example`whoami`.com",
        operation="child_process.exec",
        context=Context2(),
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
