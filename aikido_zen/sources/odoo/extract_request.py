from uuid import UUID

from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger

PLAIN_ROUTE_TYPES = (str, int, float, bool)


def _store(context, source, value):
    if source == "body":
        context.set_body(value)
    else:
        setattr(context, source, value)
    # Odoo runs its own SQL before it reads the request, and that caches the old values.
    context.parsed_userinput.pop(source, None)
    context.set_as_current_context()


def _add_value(merged, key, value):
    previous = merged.setdefault(key, value)
    values = previous if isinstance(previous, list) else [previous]
    if value not in values:
        merged[key] = values + [value]


def _merged(values, more):
    if more == values:
        return values
    # A set keeps this linear, because a client can repeat one name thousands of times.
    known = set(values)
    merged = list(values)
    for value in more:
        if value not in known:
            known.add(value)
            merged.append(value)
    return merged


def _request_context(httprequest):
    # The Werkzeug hook also runs for Flask requests and another request's body read.
    context_ref = getattr(httprequest, "environ", {}).get("aikido_zen.odoo_context")
    context = context_ref() if context_ref is not None else None
    return context if context is get_current_context() else None


def _save_query_and_cookies(context, httprequest):
    """Adds Odoo's parse of the query and cookies next to Zen's own parse."""
    query = dict(context.query or {})
    for key, values in httprequest.args.lists():
        query[key] = _merged(query.get(key, []), values)
    if query != context.query:
        _store(context, "query", query)

    cookies = dict(context.cookies or {})
    for key, values in httprequest.cookies.lists():
        previous = cookies.get(key, [])
        if isinstance(previous, str):
            previous = [previous]
        merged = _merged(previous, values)
        cookies[key] = merged[0] if len(merged) == 1 else merged
    if cookies != context.cookies:
        _store(context, "cookies", cookies)


def save_route_args(route_args):
    context = get_current_context()
    if not context or not isinstance(route_args, dict) or not route_args:
        return
    try:
        existing = context.route_params or {}
        # Odoo's values hold text after ";" that the URL segments do not.
        if isinstance(existing, list):
            existing = {"url_segments": existing}
        merged = dict(existing)
        for key, value in route_args.items():
            if isinstance(value, UUID):
                value = str(value)
            # Record converters pass Odoo records, and comparing one runs SQL.
            # Their URL text is still scanned as a URL segment.
            if type(value) in PLAIN_ROUTE_TYPES:
                _add_value(merged, key, value)
        _store(context, "route_params", merged)
    except Exception as exc:
        logger.debug("Exception occurred whilst extracting odoo route args: %s", exc)


def save_body(httprequest, data):
    context = _request_context(httprequest)
    if not context:
        return
    try:
        _save_query_and_cookies(context, httprequest)
        form = httprequest.__dict__.get("form")
        files = httprequest.__dict__.get("files")
        if form or files:
            body = form.to_dict(flat=False) if form else {}
            if files:
                for key, upload in files.items(multi=True):
                    if upload.filename:
                        body.setdefault(key, []).append(upload.filename)
        elif context.body is None:
            body = data
        else:
            return
        if body != context.body:
            _store(context, "body", body)
    except Exception as exc:
        logger.debug("Exception occurred whilst extracting odoo request data: %s", exc)


def save_rpc_params(params):
    context = get_current_context()
    # A text body is the raw XML-RPC request; JSON-RPC stored its parsed body already.
    raw_or_empty = context and (context.body is None or isinstance(context.body, str))
    if raw_or_empty and params is not None:
        _store(context, "body", params)
