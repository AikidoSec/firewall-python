import gzip
import json
import socket
import urllib.request
import urllib.error

from aikido_zen.background_process.requests.errors import TimeoutExceeded


def make_request(method, url, timeout, data=None, headers=None):
    req = urllib.request.Request(url, data=data, method=method)

    # Add headers
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return Response(response)
    except urllib.error.HTTPError as e:
        return FailedResponse(status_code=e.code)
    except socket.timeout:
        raise TimeoutExceeded()


class Response:
    def __init__(self, response):
        self.status_code = response.getcode()
        if response.info().get("Content-Encoding") == "gzip":
            # we need to do the gzip decoding ourselves, since urllib has no native support.
            self.text = decode_gzip(response.read())
        else:
            self.text = response.read().decode("utf-8")

    def json(self):
        return json.loads(self.text)


class FailedResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.text = ""


def decode_gzip(raw_bytes, encoding="utf-8"):
    f = gzip.decompress(raw_bytes)
    return f.decode(encoding)
