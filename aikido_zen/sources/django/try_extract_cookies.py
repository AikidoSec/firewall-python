from aikido_zen.helpers.logging import logger
def try_extract_cookies_from_django_request(request):
    try:
        # https://github.com/django/django/blob/7091801e046dc85dba2238ed4eaf0b3f62bcfc7f/django/core/handlers/wsgi.py#L100
        # https://github.com/django/django/blob/7091801e046dc85dba2238ed4eaf0b3f62bcfc7f/django/core/handlers/asgi.py#L131
        cookies = request.COOKIES
        return cookies
    except Exception as e:
        logger.debug("Exception occurred trying to extract django cookies: %s", e)
