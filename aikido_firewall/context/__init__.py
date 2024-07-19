"""
Provides all the functionality for contexts
"""

import threading

local = threading.local()


def get_current_context():
    """Returns the current context"""
    try:
        return local.current_context
    except AttributeError:
        return None


def parse_headers(headers):
    """Parse EnvironHeaders object into a dict"""
    return dict(zip(headers.keys(), headers.values()))


class Context:
    """
    A context object, it stores everything that is important
    for vulnerability detection
    """

    def __init__(self, req):
        self.method = req.method
        self.remote_address = req.remote_addr
        self.url = req.url
        self.body = req.form.to_dict()
        self.headers = parse_headers(req.headers)
        self.query = req.args.to_dict()
        self.cookies = req.cookies.to_dict()
        self.source = "flask"

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
