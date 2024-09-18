import pytest
from .get_api_info import get_api_info


class Context:
    def __init__(
        self,
        method,
        path,
        body={},
        xml={},
        query={},
        content_type="application/x-www-form-urlencoded",
    ):
        self.method = method
        self.path = path
        self.body = body
        self.xml = xml
        self.headers = {"CONTENT_TYPE": content_type}
        self.query = query
        self.cookies = {}


def test_get_api_info_with_form_encoded_context(monkeypatch):
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
    api_info = get_api_info(context1)
    assert api_info == {
        "body": {
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
        },
        "auth": None,
        "query": None,
    }


def test_get_api_info_with_json(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")
    context1 = Context(
        "GET",
        "/api/resource1",
        body={
            "user": {"name": "John Doe", "email": "john.doe@example.com"},
        },
        query={
            "user2": {"nickname": "John Doe", "mail": "john.doe@example.com"},
        },
        content_type="application/json",
    )
    api_info = get_api_info(context1)
    assert api_info == {
        "body": {
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
        },
        "query": {
            "properties": {
                "user2": {
                    "properties": {
                        "mail": {
                            "type": "string",
                        },
                        "nickname": {
                            "type": "string",
                        },
                    },
                    "type": "object",
                },
            },
            "type": "object",
        },
        "auth": None,
    }


def test_auth_get_api_info(monkeypatch):
    monkeypatch.setenv("AIKIDO_FEATURE_COLLECT_API_SCHEMA", "1")
    context1 = Context(
        "GET",
        "/api/resource1",
        body={
            "user": {"name": "John Doe", "email": "john.doe@example.com"},
        },
        query={
            "user2": {"nickname": "John Doe", "mail": "john.doe@example.com"},
        },
        content_type="application/json",
    )
    context1.headers["AUTHORIZATION"] = "Bearer token"
    api_info = get_api_info(context1)
    assert api_info == {
        "body": {
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
        },
        "query": {
            "properties": {
                "user2": {
                    "properties": {
                        "mail": {
                            "type": "string",
                        },
                        "nickname": {
                            "type": "string",
                        },
                    },
                    "type": "object",
                },
            },
            "type": "object",
        },
        "auth": [{"scheme": "bearer", "type": "http"}],
    }
