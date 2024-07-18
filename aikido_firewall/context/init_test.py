import pytest
from aikido_firewall.context import Context, get_current_context
@pytest.fixture
def sample_request():
    # Mock a sample request object for testing
    class Request:
        def __init__(self):
            self.method = 'GET'
            self.remote_addr = '127.0.0.1'
            self.url = '/test'
            self.form = {}
            self.headers = {}
            self.args = {}
            self.cookies = {}
    
    return Request()

def test_get_current_context_no_context():
    # Test get_current_context() when no context is set
    assert get_current_context() is None

def test_set_as_current_context(sample_request):
    # Test set_as_current_context() method
    context = Context(sample_request)
    context.set_as_current_context()
    assert get_current_context() == context

def test_get_current_context_with_context(sample_request):
    # Test get_current_context() when a context is set
    context = Context(sample_request)
    context.set_as_current_context()
    assert get_current_context() == context
