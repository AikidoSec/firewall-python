"""
Provides all the functionality for contexts
"""

import threading

SUPPORTED_SOURCES = ["django", "flask"]
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
        if source == "flask":
            self.remote_address = req.remote_addr
        elif source == "django":
            self.remote_address = req.META.get("REMOTE_ADDR")

        if source == "flask":
            self.url = req.url
        elif source == "django":
            self.url = req.build_absolute_uri()

        if source == "flask":
            self.body = req.form.to_dict()
        elif source == "django":
            self.body = dict(req.POST)

        self.headers = parse_headers(req.headers)
        if source == "flask":
            self.query = req.args.to_dict()
        elif source == "django":
            self.query = dict(req.GET)

        if source == "flask":
            self.cookies = req.cookies.to_dict()
        elif source == "django":
            self.cookies = req.COOKIES

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
