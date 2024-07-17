"""
Provides all the functionality for contexts
"""
from werkzeug.wrappers import Request

class Context:
    """
    A context object, it stores everything that is important
    for vulnerability detection
    """
    def __init__(self, environ):
        request = Request(environ)
        self.method = request.method
        self.remote_address = request.remote_addr
        self.url = request.url
        self.body = request.form
        self.headers = request.headers
        self.query = request.args
        self.cookies = request.cookies
        self.source = "flask"
