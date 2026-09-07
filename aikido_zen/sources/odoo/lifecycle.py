from aikido_zen.context import Context, current_context, get_current_context
from aikido_zen.errors import AikidoException
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.logging import logger
from aikido_zen.sinks import patch_function
from aikido_zen.sources.functions.request_handler import request_handler
from .body import extract_body
from .route import extract_route_arguments


_SUPPORTED_MAJOR_VERSIONS = {16, 17, 18, 19}
_PATCH_MARKER = "_aikido_zen_request_source_patched"
_PRE_DISPATCH_MARKER = "_aikido_zen_pre_dispatch_handled"
_POST_DISPATCH_MARKER = "_aikido_zen_post_dispatch_handled"


class _ContextPreservingIterable:
    def __init__(self, iterable, context):
        self.iterable = iterable
        self.context = context
        self.iterator = None

    def __iter__(self):
        return self

    def __next__(self):
        token = current_context.set(self.context)
        try:
            if self.iterator is None:
                self.iterator = iter(self.iterable)
            return next(self.iterator)
        finally:
            current_context.reset(token)

    def close(self):
        token = current_context.set(self.context)
        try:
            close = getattr(self.iterable, "close", None)
            if not callable(close):
                return None
            return close()
        finally:
            current_context.reset(token)

    def __getattr__(self, name):
        return getattr(self.iterable, name)


def _request_init(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    try:
        httprequest = getattr(instance, "httprequest", None)
        environ = getattr(httprequest, "environ", None)
        if environ is None:
            return result

        context = Context(req=environ, source="odoo")
        context.set_as_current_context()
        request_handler(stage="init")
    except AikidoException:
        raise
    except Exception:
        logger.debug("Failed to initialize the Odoo request context.")
    return result


def _dispatcher_pre_dispatch(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    context = get_current_context()
    if context is None or context.source != "odoo":
        return result
    if getattr(context, _PRE_DISPATCH_MARKER, False):
        return result
    setattr(context, _PRE_DISPATCH_MARKER, True)

    route_arguments = get_argument(args, kwargs, 1, "args")

    try:
        context.route_params = extract_route_arguments(route_arguments)
        context.parsed_userinput.pop("route_params", None)
    except AikidoException:
        raise
    except Exception:
        logger.debug("Failed to extract the Odoo route arguments.")

    try:
        body = extract_body(instance.request, getattr(instance, "routing_type", None))
        context.set_body(body)
        context.parsed_userinput.pop("body", None)
    except AikidoException:
        raise
    except Exception:
        logger.debug("Failed to extract the Odoo request body.")

    response = _request_policy_response(instance.request)
    if response is not None:
        _abort_with_response(response)
    return result


def _request_policy_response(request):
    try:
        pre_response = request_handler(stage="pre_response")
        if pre_response is not None:
            message, status_code = pre_response
            return _make_plain_text_response(request, message, status_code)

    except AikidoException:
        raise
    except Exception:
        logger.debug("Failed to evaluate Odoo request policies.")
    return None


def _make_plain_text_response(request, message, status_code):
    return request.make_response(
        message,
        headers=[("Content-Type", "text/plain; charset=utf-8")],
        status=status_code,
    )


def _abort_with_response(response):
    try:
        from werkzeug.exceptions import HTTPException, abort
    except Exception:
        logger.debug("Failed to import Werkzeug while blocking an Odoo request.")
        return

    try:
        abort(response)
    except (AikidoException, HTTPException):
        raise
    except Exception:
        logger.debug("Failed to abort a blocked Odoo request.")


def _record_response(context, status_code):
    if context is None or context.source != "odoo":
        return
    if getattr(context, _POST_DISPATCH_MARKER, False):
        return

    setattr(context, _POST_DISPATCH_MARKER, True)
    try:
        request_handler(stage="post_response", status_code=status_code)
    except AikidoException:
        raise
    except Exception:
        logger.debug("Failed to process the Odoo response.")


def _dispatcher_post_dispatch(wrapped, instance, args, kwargs):
    result = wrapped(*args, **kwargs)
    response = get_argument(args, kwargs, 0, "response")
    try:
        status_code = getattr(response, "status_code")
    except Exception:
        logger.debug("Failed to read the Odoo response status.")
        return result

    if status_code is not None:
        _record_response(get_current_context(), status_code)
    return result


def _application_call(wrapped, instance, args, kwargs):
    start_response = get_argument(args, kwargs, 1, "start_response")
    application_args = args
    application_kwargs = kwargs

    if callable(start_response):

        def record_start_response(status, headers, *extra):
            try:
                status_code = int(status.split(" ", 1)[0])
            except (AttributeError, TypeError, ValueError):
                logger.debug("Failed to read the Odoo WSGI response status.")
            else:
                _record_response(get_current_context(), status_code)
            return start_response(status, headers, *extra)

        if "start_response" in kwargs:
            application_kwargs = {**kwargs, "start_response": record_start_response}
        elif len(args) > 1:
            application_args = (*args[:1], record_start_response, *args[2:])

    previous_context = get_current_context()
    entry_token = current_context.set(previous_context)
    try:
        iterable = wrapped(*application_args, **application_kwargs)
        request_context = get_current_context()
    finally:
        current_context.reset(entry_token)

    if request_context is previous_context:
        return iterable
    if request_context is None or request_context.source != "odoo":
        return iterable
    return _ContextPreservingIterable(iterable, request_context)


def _get_major_version(http_module):
    try:
        return int(http_module.odoo.release.version_info[0])
    except (AttributeError, IndexError, TypeError, ValueError):
        return None


def _has_required_lifecycle(http_module):
    required_methods = (
        ("Request", "__init__"),
        ("Dispatcher", "pre_dispatch"),
        ("Dispatcher", "post_dispatch"),
        ("Application", "__call__"),
    )
    return all(
        callable(getattr(getattr(http_module, class_name, None), method_name, None))
        for class_name, method_name in required_methods
    )


def is_patched(http_module):
    return getattr(http_module, _PATCH_MARKER, False) is True


def patch(http_module):
    if is_patched(http_module):
        return True

    major_version = _get_major_version(http_module)
    if major_version not in _SUPPORTED_MAJOR_VERSIONS:
        logger.warning(
            "Odoo request protection disabled: supported Odoo versions are 16 through 19."
        )
        return False

    if not _has_required_lifecycle(http_module):
        logger.warning(
            "Odoo request protection disabled: required HTTP lifecycle hooks are unavailable."
        )
        return False

    patch_function(http_module, "Request.__init__", _request_init)
    patch_function(http_module, "Dispatcher.pre_dispatch", _dispatcher_pre_dispatch)
    patch_function(http_module, "Dispatcher.post_dispatch", _dispatcher_post_dispatch)
    patch_function(http_module, "Application.__call__", _application_call)
    setattr(http_module, _PATCH_MARKER, True)
    return True
