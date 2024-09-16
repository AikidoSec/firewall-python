import pytest
from .get_body_info import get_body_info


class Context:
    def __init__(
        self,
        method,
        path,
        body={},
        xml={},
        content_type="application/x-www-form-urlencoded",
    ):
        self.method = method
        self.path = path
        self.body = body
        self.xml = xml
        self.headers = {"CONTENT_TYPE": content_type}


def test_get_body_info_with_form_encoded_context(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")
    context1 = Context(
        "GET",
        "/api/resource1",
        body={
            "data1": {
                "data2": [{"Help": True}, {"Help": True, "location": "Sea"}],
                "identifier": "hsfkjewhfwehgkjwehgkj",
                "active": True,
            },
            "user": {"name": "John Doe", "email": "john.doe@example.com"},
        },
    )
    body_info = get_body_info(context1)
    assert body_info == {
        "schema": {
            "properties": {
                "data1": {
                    "properties": {
                        "active": {
                            "type": "boolean",
                        },
                        "data2": {
                            "items": {
                                "properties": {
                                    "Help": {
                                        "type": "boolean",
                                    },
                                    "location": {
                                        "optional": True,
                                        "type": "string",
                                    },
                                },
                                "type": "object",
                            },
                            "type": "array",
                        },
                        "identifier": {
                            "type": "string",
                        },
                    },
                    "type": "object",
                },
                "user": {
                    "properties": {
                        "email": {
                            "type": "string",
                        },
                        "name": {
                            "type": "string",
                        },
                    },
                    "type": "object",
                },
            },
            "type": "object",
        },
        "type": "form-urlencoded",
    }


def test_get_body_info_with_json(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")
    context1 = Context(
        "GET",
        "/api/resource1",
        body={
            "user": {"name": "John Doe", "email": "john.doe@example.com"},
        },
        content_type="application/json",
    )
    body_info = get_body_info(context1)
    assert body_info == {
        "schema": {
            "properties": {
                "user": {
                    "properties": {
                        "email": {
                            "type": "string",
                        },
                        "name": {
                            "type": "string",
                        },
                    },
                    "type": "object",
                },
            },
            "type": "object",
        },
        "type": "json",
    }
