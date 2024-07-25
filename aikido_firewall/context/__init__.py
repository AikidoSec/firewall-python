"""
Provides all the functionality for contexts
"""

import threading

SUPPORTED_SOURCES = ["django", "flask"]
UINPUT_SOURCES = ["body", "cookies", "query", "headers"]

local = threading.local()


def get_current_context():
    """Returns the current context"""
    try:
        return local.current_context
    except AttributeError:
        return None


def parse_headers(headers):
    """Parse EnvironHeaders object into a dict"""
    if isinstance(headers, dict):
        return headers
    return dict(zip(headers.keys(), headers.values()))


class Context:
    """
    A context object, it stores everything that is important
    for vulnerability detection
    """

    def __init__(self, req, source):
        if not source in SUPPORTED_SOURCES:
            raise ValueError(f"Source {source} not supported")
        self.source = source
        self.method = req.method
        self.headers = parse_headers(req.headers)
        if source == "flask":
            self.set_flask_attrs(req)
        elif source == "django":
            self.set_django_attrs(req)

    def set_django_attrs(self, req):
        """set properties that are specific to django"""
        self.remote_address = req.META.get("REMOTE_ADDR")
        self.url = req.build_absolute_uri()
        self.body = dict(req.POST)
        self.query = dict(req.GET)
        self.cookies = req.COOKIES

    def set_flask_attrs(self, req):
        """Set properties that are specific to flask"""
        self.remote_address = req.remote_addr
        self.url = req.url
        self.body = req.form.to_dict()
        self.query = req.args.to_dict()
        self.cookies = req.cookies.to_dict()

    def __reduce__(self):
        return (
            self.__class__,
            (
                self.method,
                self.remote_address,
                self.url,
                self.body,
                self.headers,
                self.query,
                self.cookies,
                self.source,
            ),
        )

    def set_as_current_context(self):
        """
        Set the current context
        """
        local.current_context = self
