"""
Records whether the current request's remote IP is in the bypass list.

Bypassed requests intentionally do not set a Context (so all per-request
protection short-circuits), but checks that run without a Context — for
example outbound DNS reporting — still need a way to detect "this work
was triggered by a bypassed request".
"""

import contextvars

_bypassed = contextvars.ContextVar("aikido_bypassed_ip", default=False)


def set_bypassed(value: bool) -> None:
    _bypassed.set(bool(value))


def is_bypassed() -> bool:
    try:
        return _bypassed.get()
    except Exception:
        return False


def clear() -> None:
    _bypassed.set(False)
