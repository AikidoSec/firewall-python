from enum import Enum
from json import dumps as json_dumps
from json import loads as json_loads
import urllib.request
import urllib.error
from urllib.error import HTTPError

from aikido_zen.helpers.logging import logger


class InternalRequest:
    @staticmethod
    def get(url, headers=None, timeout=3):
        try:
            raw_response = InternalRequest._request(
                "GET", url, headers=headers, timeout=timeout
            )
            return Response(raw_response)
        except Exception as e:
            return Response(RawInternalResponse(0, str(e), url))

    @staticmethod
    def post(url, json=None, headers=None, timeout=3):
        try:
            data = None
            if headers is not None:
                headers = headers
            if json is not None:
                data = json_dumps(json).encode("utf-8")
                headers["Content-Type"] = "application/json"

            raw_response = InternalRequest._request("POST", url, data, headers, timeout)
            return Response(raw_response)
        except Exception as e:
            return Response(RawInternalResponse(0, str(e), url))

    @staticmethod
    def _request(method, url, data=None, headers=None, timeout=3):
        req = urllib.request.Request(url, data=data, method=method)

        # Add headers
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return RawInternalResponse(
                    response.getcode(), response.read().decode("utf-8"), url
                )
        except HTTPError as e:
            return RawInternalResponse(e.code, e.read().decode("utf-8"), url)


class RawInternalResponse:
    def __init__(self, status_code, text, url):
        self.status_code = status_code
        self.text = text
        self.url = url


class ResponseError(Enum):
    TIMEOUT_ERROR = "timeout"
    INVALID_TOKEN = "invalid_token"
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"
    JSON_PARSING_FAILED = "json_parsing_failed"
    MAX_ATTACKS_REACHED = "max_attacks_reached"


class Response:
    def __init__(self, raw_response: RawInternalResponse):
        self.status_code = raw_response.status_code
        self.raw_data = raw_response.text
        self.success = False
        self.error = None

        # Try parsing as JSON, if parsing is successful, set success to True
        if 200 <= self.status_code <= 299:
            try:
                self.json = json_loads(self.raw_data)
                self.success = True
            except Exception as e:
                self.raw_data = str(e)
                self.error = ResponseError.JSON_PARSING_FAILED

        if self.success or self.error:
            return

        # If there was an error, try to handle it here
        self.error = ResponseError.UNKNOWN
        if self.status_code == 429:
            # Happens when core is getting too many requests at the same time
            self.error = ResponseError.RATE_LIMITED
        elif self.status_code == 401:
            # Happens when the token the user provided in AIKIDO_TOKEN is invalid
            self.error = ResponseError.INVALID_TOKEN
        elif self.status_code == 0 and self.raw_data == "max_attacks_reached":
            self.error = ResponseError.MAX_ATTACKS_REACHED

        logger.info(
            "Error parsing API Response for %s: %s (%s) %s",
            raw_response.url,
            raw_response.status_code,
            self.error.value,
            raw_response.text,
        )

    def __str__(self):
        if self.success:
            return (
                f"SuccessfulResponse<status: {self.status_code}, data: {self.raw_data}>"
            )
        return f"FailedResponse<error: {self.error.value}, data: {self.raw_data}>"
