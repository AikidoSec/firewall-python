import pytest
from aikido_zen.context import current_context, Context, get_current_context
from aikido_zen.thread.thread_cache import ThreadCache, threadlocal_storage
from . import should_block_request


def test_without_context():
    current_context.set(None)
    assert should_block_request() == {"block": False}


def test_with_context_without_cache():
    Context(
        context_obj={
            "remote_address": "::1",
            "method": "POST",
            "url": "http://localhost:4000",
            "query": {
                "abc": "def",
            },
            "headers": {},
            "body": None,
            "cookies": {},
            "source": "flask",
            "route": "/posts/:id",
        }
    ).set_as_current_context()
    threadlocal_storage.cache = None
    assert should_block_request() == {"block": False}


def test_with_context_with_cache():
    Context(
        context_obj={
            "remote_address": "::1",
            "method": "POST",
            "url": "http://localhost:4000",
            "query": {
                "abc": "def",
            },
            "headers": {},
            "body": None,
            "cookies": {},
            "source": "flask",
            "route": "/posts/:id",
            "user": {"id": "123"},
            "executed_middleware": False,
        }
    ).set_as_current_context()
    thread_cache = ThreadCache()

    thread_cache.config.blocked_uids = ["123"]
    assert get_current_context().executed_middleware == False
    assert should_block_request() == {
        "block": True,
        "trigger": "user",
        "type": "blocked",
    }
    assert get_current_context().executed_middleware == True

    thread_cache.config.blocked_uids = []
    assert should_block_request() == {"block": False}

    thread_cache.config.blocked_uids = ["23", "234", "456"]
    assert should_block_request() == {"block": False}
    assert get_current_context().executed_middleware == True
