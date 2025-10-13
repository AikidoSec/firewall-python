from aikido_zen.context import Context
from aikido_zen.helpers.headers import Headers


def generate_and_set_context(*args, **kwargs) -> Context:
    context = generate_context(*args, **kwargs)
    context.set_as_current_context()
    return context


def generate_context(value=None, query_value=None) -> Context:
    context = MockTestContext()

    if value is not None:
        context.body["key1"] = value
    if query_value is not None:
        context.query["key1"] = query_value

    return context


class MockTestContext(Context):
    def __init__(self):
        self.cookies = {}
        self.headers = Headers()
        self.remote_address = "1.1.1.1"
        self.method = "POST"
        self.url = "url"
        self.body = {}
        self.query = {}
        self.source = "flask"
        self.route = "/"
        self.parsed_userinput = {}
        self.user = None
        self.rate_limit_group = None
        self.executed_middleware = False
