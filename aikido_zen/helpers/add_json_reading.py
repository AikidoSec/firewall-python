"""Exports add_json_reading"""

import json


def add_json_reading(form, raw_body):
    """Returns [json, form] when the form body is also JSON the app may json.loads()."""
    start = raw_body.lstrip()[:1]
    # json.loads also accepts a BOM or UTF-16/32, which start with non-ASCII or NUL.
    if start.isascii() and start not in (b"\x00", b"{", b"[", b'"'):
        return form
    try:
        return [json.loads(raw_body), form]
    except (ValueError, RecursionError):
        return form
