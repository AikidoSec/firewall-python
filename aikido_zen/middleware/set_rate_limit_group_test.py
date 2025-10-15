import pytest
from aikido_zen.thread.thread_cache import get_cache
import aikido_zen.test_utils as test_utils
from .set_rate_limit_group import set_rate_limit_group


@pytest.fixture(autouse=True)
def run_around_tests():
    get_cache().reset()
    yield
    # Reset context and cache after every test
    from aikido_zen.context import current_context

    current_context.set(None)
    get_cache().reset()


def test_set_rate_limit_group_valid_group_id(caplog):
    context1 = test_utils.generate_and_set_context()
    assert context1.rate_limit_group is None
    set_rate_limit_group("group1")
    assert context1.rate_limit_group == "group1"
    assert "Group ID cannot be empty." not in caplog.text
    assert "was called without a context" not in caplog.text
    assert "must be called before the Zen middleware is executed" not in caplog.text


def test_set_rate_limit_group_empty_group_id(caplog):
    context1 = test_utils.generate_and_set_context()
    assert context1.rate_limit_group is None
    set_rate_limit_group("")
    assert context1.rate_limit_group is None
    assert "Group ID cannot be empty." in caplog.text


def test_set_rate_limit_group_none_group_id(caplog):
    context1 = test_utils.generate_and_set_context()
    assert context1.rate_limit_group is None
    set_rate_limit_group(None)
    assert context1.rate_limit_group is None
    assert "Group ID cannot be empty." in caplog.text


def test_set_rate_limit_group_no_context(caplog):
    from aikido_zen.context import current_context

    current_context.set(None)
    set_rate_limit_group("group1")
    assert "was called without a context" in caplog.text


def test_set_rate_limit_group_middleware_already_executed(caplog):
    context1 = test_utils.generate_and_set_context()
    context1.executed_middleware = True
    set_rate_limit_group("group1")
    assert "must be called before the Zen middleware is executed" in caplog.text
    assert context1.rate_limit_group is "group1"


def test_set_rate_limit_group_non_string_group_id(caplog):
    context1 = test_utils.generate_and_set_context()
    assert context1.rate_limit_group is None
    set_rate_limit_group(123)
    assert context1.rate_limit_group == "123"


def test_set_rate_limit_group_non_string_group_id_non_number(caplog):
    context1 = test_utils.generate_and_set_context()
    assert context1.rate_limit_group is None
    set_rate_limit_group({"a": "b"})
    assert context1.rate_limit_group is None
    assert "Group ID must be a string or a number" in caplog.text


def test_set_rate_limit_group_overwrite_existing_group():
    context1 = test_utils.generate_and_set_context()
    assert context1.rate_limit_group is None
    set_rate_limit_group("group1")
    assert context1.rate_limit_group == "group1"
    set_rate_limit_group("group2")
    assert context1.rate_limit_group == "group2"
