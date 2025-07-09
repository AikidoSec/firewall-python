from typing import Dict, Optional

from aikido_zen.helpers.logging import logger


def extract_cookies_from_django_request(request) -> Optional[Dict[str, str]]:
    try:
        return _extract_cookies_from_django_request(request)
    except Exception as e:
        logger.debug("Failed to extract cookies from django request: %s", e)


def _extract_cookies_from_django_request(request) -> Dict[str, str]:
    # https://github.com/django/django/blob/7091801e046dc85dba2238ed4eaf0b3f62bcfc7f/django/core/handlers/wsgi.py#L100
    # https://github.com/django/django/blob/7091801e046dc85dba2238ed4eaf0b3f62bcfc7f/django/core/handlers/asgi.py#L131
    # request.COOKIES is not a MultiValueDict, it's a normal dictionary
    return getattr(request, "COOKIES", {})
