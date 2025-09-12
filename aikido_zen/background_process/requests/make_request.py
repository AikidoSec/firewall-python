import json
import urllib


def make_request(method, url, data=None, headers=None, timeout=3):
    req = urllib.request.Request(url, data=data, method=method)

    # Add headers
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)

    with urllib.request.urlopen(req, timeout=timeout) as response:
        return Response(
            status_code=response.getcode(), data=response.read().decode("utf-8")
        )


class Response:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self.data = data

    def json(self):
        return json.loads(self.data)
