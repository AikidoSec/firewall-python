from functools import partial
from contextvars import copy_context
from weakref import proxy, ref

from aikido_zen.context import Context, get_current_context
from aikido_zen.helpers.get_argument import get_argument
from aikido_zen.helpers.lazy_body_stream import LazyBodyStream
from aikido_zen.sinks import (
    on_import,
    patch_function,
    before_modify_return,
    before,
    after,
)
from .extract_cookies import extract_cookies_from_flask_request_and_save_data
from .extract_form_data import extract_body_from_flask_request
from .extract_query import extract_query_from_flask_request_and_save_data
from .extract_view_args import extract_view_args_from_flask_request_and_save_data
import aikido_zen.sources.functions.request_handler as funcs
from aikido_zen.sources.functions.request_handler import pre_response as should_block


@before_modify_return
def _full_dispatch_request_before(func, instance, args, kwargs):
    from flask.globals import request_ctx

    req = request_ctx.request
    extract_cookies_from_flask_request_and_save_data(req)
    extract_view_args_from_flask_request_and_save_data(req)
    extract_query_from_flask_request_and_save_data(req)
    context = get_current_context()
    if context is not None and (
        req.content_length or req.environ.get("wsgi.input_terminated")
    ):
        context.set_body_loader(partial(extract_body_from_flask_request, proxy(req)))
        req.environ["aikido_zen.body_context"] = ref(context)
        req.environ["wsgi.input"] = LazyBodyStream(
            req.environ["wsgi.input"], context.load_body
        )
        req.__dict__["stream"] = LazyBodyStream(req.stream, context.load_body)


@after
def _full_dispatch_request_after(func, instance, args, kwargs, return_value):
    if not hasattr(return_value, "status_code"):
        return
    context = get_current_context()
    if context is not None and "_body_loader" in context.__dict__:
        from flask import has_request_context
        from flask.globals import request_ctx
        from werkzeug.wsgi import ClosingIterator

        # Response generators can need these bindings after Flask pops them.
        saved_context = copy_context()
        request_ref = ref(request_ctx.request)
        loader = context.__dict__["_body_loader"]

        def load_body():
            try:
                if saved_context is not None:
                    return saved_context.run(loader)
                return loader()
            finally:
                # Deferred parsing can open uploads after Flask's request cleanup.
                if (
                    not has_request_context()
                    or request_ctx.request is not request_ref()
                ):
                    req = request_ref()
                    if req is not None:
                        req.close()

        def release_request_context():
            nonlocal saved_context
            saved_context = None

        context.set_body_loader(load_body)
        if return_value.direct_passthrough:
            return_value.response = ClosingIterator(
                return_value.response, release_request_context
            )
        else:
            return_value.call_on_close(release_request_context)
    funcs.request_handler(stage="post_response", status_code=return_value.status_code)


@before
def _read_body_before(func, instance, args, kwargs):
    context_ref = instance.environ.get("aikido_zen.body_context")
    context = context_ref() if context_ref is not None else None
    if context is not None:
        context.load_body()


@before_modify_return
def _call(func, instance, args, kwargs):
    environ = get_argument(args, kwargs, 0, "environ")
    start_response = get_argument(args, kwargs, 1, "start_response")

    context1 = Context(req=environ, source="flask")
    context1.set_as_current_context()
    funcs.request_handler(stage="init")

    # Checks for blocked IPs, blocked UAs, ...
    should_block_current_request = should_block()
    if should_block_current_request is not None:
        from flask import Response

        msg, status_code = should_block_current_request
        return Response(msg, status=status_code, mimetype="text/plain")(
            environ, start_response
        )


@on_import("flask.app", "flask", version_requirement="2.2.4")
def patch(m):
    """
    patching module flask.appimport

    - patches: Flask.__call__, also done by Sentry.
    - patches: Flask.full_dispatch_request
    **Why?** full_dispatch_request gets called in the WSGI app. It gets called after all middleware. request_ctx is
    available, so we can extract data from it.
    (github src: https://github.com/pallets/flask/blob/bc143499cf1137a271a7cf75bdd3e16e43ede2f0/src/flask/app.py#L1529)
    """
    patch_function(m, "Flask.__call__", _call)
    patch_function(m, "Flask.full_dispatch_request", _full_dispatch_request_before)
    patch_function(m, "Flask.full_dispatch_request", _full_dispatch_request_after)


@on_import("flask.wrappers", "flask", version_requirement="2.2.4")
def patch_request(m):
    patch_function(m, "Request.get_data", _read_body_before)
    patch_function(m, "Request._load_form_data", _read_body_before)
