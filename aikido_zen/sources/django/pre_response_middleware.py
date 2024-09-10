"""Exports pre_response_middleware function"""

from ..functions.request_handler import request_handler


def pre_response_middleware(request, *args, **kwargs):
    """Aikido middleware that handles ratelimiting"""
    response = request_handler(stage="pre_response")
    if response:
        # pylint:disable=import-outside-toplevel # We don't want to install this by default
        from django.http import HttpResponse

        return HttpResponse(response[0], status=response[1])
    return None
