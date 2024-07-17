"""
Provides all the functionality for contexts
"""


class Context:
    """
    A context object, it stores everything that is important
    for vulnerability detection
    """

    def __init__(self, req):
        self.method = req.method
        self.remote_address = req.remote_addr
        self.url = req.url
        self.body = req.form
        self.headers = req.headers
        self.query = req.args
        self.cookies = req.cookies
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
