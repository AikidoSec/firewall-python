from aikido_zen.background_process.requests.make_request import make_request
from json import dumps as json_dumps


def get(url, headers=None, timeout=3):
    return make_request("GET", url, headers=headers, timeout=timeout)


def post(url, json=None, headers=None, timeout=3):
    data = None
    if headers is None:
        headers = {}
    if json is not None:
        data = json_dumps(json).encode("utf-8")
        headers["Content-Type"] = "application/json"

    return make_request("POST", url, data, headers, timeout)
