import pytest
from .merge_auth_types import merge_auth_types as merge


def test_merge_api_auth_types():
    result = merge(
        [
            {
                "type": "http",
                "scheme": "bearer",
            },
            {
                "type": "apiKey",
                "in": "header",
                "name": "x-api-key",
            },
        ],
        [
            {
                "type": "http",
                "scheme": "bearer",
            },
            {
                "type": "http",
                "scheme": "basic",
            },
            {
                "type": "apiKey",
                "in": "header",
                "name": "x-api-key-v2",
            },
        ],
    )
    assert result == [
        {
            "type": "http",
            "scheme": "bearer",
        },
        {
            "type": "apiKey",
            "in": "header",
            "name": "x-api-key",
        },
        {
            "type": "http",
            "scheme": "basic",
        },
        {
            "type": "apiKey",
            "in": "header",
            "name": "x-api-key-v2",
        },
    ]

    assert merge(None, None) is None

    assert merge(
        [
            {
                "type": "http",
                "scheme": "bearer",
            },
        ],
        None,
    ) == [
        {
            "type": "http",
            "scheme": "bearer",
        },
    ]

    assert merge(
        None,
        [
            {
                "type": "http",
                "scheme": "digest",
            },
        ],
    ) == [
        {
            "type": "http",
            "scheme": "digest",
        },
    ]


# To run the tests, use the command: pytest <filename>.py
