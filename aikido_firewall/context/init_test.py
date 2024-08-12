import pytest
import pickle
from aikido_firewall.context import Context, get_current_context


def test_get_current_context_no_context():
    # Test get_current_context() when no context is set
    assert get_current_context() is None


"""
def test_set_as_current_context(mocker):
    # Test set_as_current_context() method
    sample_request = mocker.MagicMock()
    context = Context(req=sample_request, )
    context.set_as_current_context()
    assert get_current_context() == context


def test_get_current_context_with_context(mocker):
    # Test get_current_context() when a context is set
    sample_request = mocker.MagicMock()
    context = Context(req=sample_request, source="flask")
    context.set_as_current_context()
    assert get_current_context() == context

def test_context_is_picklable(mocker):
    pickled_obj = pickle.dumps(context)
    unpickled_obj = pickle.loads(pickled_obj)
    assert unpickled_obj.source == "django"
    assert unpickled_obj.method == "POST"
    assert unpickled_obj.remote_address == "127.0.0.1"
    assert unpickled_obj.url == "http://example.com"
    assert unpickled_obj.body == {"key": "value"}
    assert unpickled_obj.headers == {"Content-Type": "application/json"}
    assert unpickled_obj.query == {"key": "value"}
    assert unpickled_obj.cookies == {"cookie": "value"}
"""
