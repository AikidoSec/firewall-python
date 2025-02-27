"""Exports pre_response_middleware function"""

from ..functions.check_if_request_is_blocked import check_if_request_is_blocked


def pre_response_middleware(request, *args, **kwargs):
    """Checks if the request should be blocked."""
    block_result = check_if_request_is_blocked()
    if block_result.blocking:
        # pylint:disable=import-outside-toplevel # We don't want to install this by default
        from django.http import HttpResponse

        return HttpResponse(block_result.message, status=block_result.status_code)
    return None
