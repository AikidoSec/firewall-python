from aikido_zen.context import Context
from aikido_zen.helpers.headers import Headers


def generate_and_set_context(*args, **kwargs) -> Context:
    context = generate_context(*args, **kwargs)
    context.set_as_current_context()
    return context


def generate_context(
    value=None,
    query_value=None,
    user=None,
    route=None,
    ip=None,
    method=None,
    url=None,
    headers=None,
) -> Context:
    context = MockTestContext()

    if value is not None:
        context.body["key1"] = value
    if query_value is not None:
        context.query["key1"] = query_value
    if user is not None:
        context.user = user
    if route is not None:
        context.route = route
    if ip is not None:
        context.remote_address = ip
    if method is not None:
        context.method = method
    if url is not None:
        context.url = url
    if headers is not None:
        for header_k, header_v in headers.items():
            context.headers.store_header(header_k, header_v)

    return context


class MockTestContext(Context):
    def __init__(self):
        super().__init__()
        self.cookies = {}
        self.headers = Headers()
        self.remote_address = "1.1.1.1"
        self.method = "POST"
        self.url = "http://localhost:8080/"
        self.body = {}
        self.query = {}
        self.source = "flask"
        self.route = "/"
        self.parsed_userinput = {}
        self.user = None
        self.rate_limit_group = None
        self.executed_middleware = False
        self.protection_forced_off = False
