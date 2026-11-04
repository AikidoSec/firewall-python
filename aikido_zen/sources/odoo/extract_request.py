from uuid import UUID

from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger

PLAIN_ROUTE_TYPES = (str, int, float, bool)


def _value_lists(mapping):
    if not mapping:
        return {}
    listed = {}
    for key, value in mapping.items():
        if isinstance(value, (list, tuple)):
            listed[key] = list(value)
        else:
            listed[key] = [value]
    return listed


def merge_listed_values(existing, framework):
    merged = _value_lists(existing)
    for key, values in _value_lists(framework).items():
        current = merged.setdefault(key, [])
        for value in values:
            if value not in current:
                current.append(value)
    return merged


def merge_cookies(existing, framework):
    merged = dict(existing or {})
    for key, value in dict(framework or {}).items():
        previous = merged.get(key)
        if previous is None or previous == value:
            merged[key] = value
            continue
        values = previous if isinstance(previous, list) else [previous]
        if value not in values:
            merged[key] = values + [value]
    return merged


def _drop_cached_strings(context, *sources):
    # Odoo's own SQL is scanned first, and that caches the old values.
    cached = getattr(context, "parsed_userinput", None)
    if not cached:
        return
    for source in sources:
        cached.pop(source, None)


def _mapping(value):
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        return value.to_dict(flat=False)
    return dict(value)


def _cookie_mapping(value):
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return dict(value)


def _form_body(httprequest):
    body = {}
    form = getattr(httprequest, "form", None)
    if form:
        body.update(_mapping(form))
    files = getattr(httprequest, "files", None)
    if not files:
        return body
    try:
        items = files.items(multi=True)
    except TypeError:
        items = files.items()
    for key, storage in items:
        filename = getattr(storage, "filename", None)
        if not filename:
            continue
        names = body.get(key, [])
        if isinstance(names, str):
            names = [names]
        if filename not in names:
            names.append(filename)
        body[key] = names
    return body


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
            # Their URL text matches only letters, digits, "-" and "_".
            if type(value) not in PLAIN_ROUTE_TYPES:
                continue
            previous = merged.get(key)
            if previous is None or previous == value:
                merged[key] = value
                continue
            values = previous if isinstance(previous, list) else [previous]
            if value not in values:
                merged[key] = values + [value]
        context.route_params = merged
        _drop_cached_strings(context, "route_params")
        context.set_as_current_context()
    except Exception as exc:
        logger.debug("Exception occurred whilst extracting odoo route args: %s", exc)


def save_parsed_request(httprequest, body=None, include_form=False):
    context = get_current_context()
    if not context or httprequest is None:
        return
    try:
        context.query = merge_listed_values(
            context.query, _mapping(getattr(httprequest, "args", None))
        )
        context.cookies = merge_cookies(
            context.cookies, _cookie_mapping(getattr(httprequest, "cookies", None))
        )
        _drop_cached_strings(context, "query", "cookies")
        if body is not None:
            context.set_body(body)
            _drop_cached_strings(context, "body")
        elif include_form:
            form_body = _form_body(httprequest)
            if form_body:
                context.set_body(form_body)
                _drop_cached_strings(context, "body")
        context.set_as_current_context()
    except Exception as exc:
        logger.debug("Exception occurred whilst extracting odoo request data: %s", exc)
