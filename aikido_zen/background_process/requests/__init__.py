from aikido_zen.background_process.requests.make_request import make_request
from json import dumps as json_dumps


def get(url, headers, timeout):
    return make_request(method="GET", url=url, headers=headers, timeout=timeout)


def post(url, json, headers, timeout):
    data = None
    if headers is None:
        headers = {}
    if json is not None:
        data = json_dumps(json).encode("utf-8")
        headers["Content-Type"] = "application/json"

    return make_request(
        method="POST", url=url, data=data, headers=headers, timeout=timeout
    )
