import pytest
import pickle
from aikido_firewall.context import Context, get_current_context


def test_get_current_context_no_context():
    # Test get_current_context() when no context is set
    assert get_current_context() is None


def test_set_as_current_context(mocker):
    # Test set_as_current_context() method
    sample_request = mocker.MagicMock()
    context = Context(req=sample_request, source="flask")
    context.set_as_current_context()
    assert get_current_context() == context


def test_get_current_context_with_context(mocker):
    # Test get_current_context() when a context is set
    sample_request = mocker.MagicMock()
    context = Context(req=sample_request, source="flask")
    context.set_as_current_context()
    assert get_current_context() == context


def test_context_init_flask(mocker):
    req = mocker.MagicMock()
    req.method = "GET"
    req.remote_addr = "127.0.0.1"
    req.url = "http://example.com"
    req.form.to_dict.return_value = {"key": "value"}
    req.headers = {"Content-Type": "application/json"}
    req.args.to_dict.return_value = {"key": "value"}
    req.cookies.to_dict.return_value = {"cookie": "value"}

    context = Context(req=req, source="flask")
    assert context.source == "flask"
    assert context.method == "GET"
    assert context.remote_address == "127.0.0.1"
    assert context.url == "http://example.com"
    assert context.body == {"key": "value"}
    assert context.headers == {"Content-Type": "application/json"}
    assert context.query == {"key": "value"}
    assert context.cookies == {"cookie": "value"}


def test_context_init_django(mocker):
    req = mocker.MagicMock()
    req.method = "POST"
    req.META.get.return_value = "127.0.0.1"
    req.build_absolute_uri.return_value = "http://example.com"
    req.POST = {"key": "value"}
    req.headers = {"Content-Type": "application/json"}
    req.GET = {"key": "value"}
    req.COOKIES = {"cookie": "value"}

    context = Context(req=req, source="django")
    assert context.source == "django"
    assert context.method == "POST"
    assert context.remote_address == "127.0.0.1"
    assert context.url == "http://example.com"
    assert context.body == {"key": "value"}
    assert context.headers == {"Content-Type": "application/json"}
    assert context.query == {"key": "value"}
    assert context.cookies == {"cookie": "value"}

def test_context_is_picklable(mocker):
    req = mocker.MagicMock()
    req.method = "POST"
    req.META.get.return_value = "127.0.0.1"
    req.build_absolute_uri.return_value = "http://example.com"
    req.POST = {"key": "value"}
    req.headers = {"Content-Type": "application/json"}
    req.GET = {"key": "value"}
    req.COOKIES = {"cookie": "value"}
    context = Context(req=req, source="django")

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
