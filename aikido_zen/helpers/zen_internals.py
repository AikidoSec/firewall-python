"""
Python bindings for the zen-internals Rust library. The library is loaded once, when
this module is imported, and every feature that uses it goes through these functions.
"""

import ctypes
import os
import platform

from aikido_zen.helpers.get_lib_path import get_binary_path
from aikido_zen.helpers.logging import logger


def _load():
    binary_path = get_binary_path()
    target = f"{platform.system().lower()}-{platform.machine().lower()}"
    if not os.path.exists(binary_path):
        logger.warning(
            "Zen will NOT block SQL injection attacks. Cannot find the zen-internals library for %s. "
            "Request support: https://github.com/AikidoSec/firewall-python/issues",
            target,
        )
        return None
    try:
        return ctypes.CDLL(binary_path)
    except OSError as e:
        logger.warning(
            "Zen will NOT block SQL injection attacks. Failed to load the zen-internals library for %s: %s",
            target,
            e,
        )
        return None


def _bind(internals_lib, name, argtypes, restype):
    """Returns the library function with its C types set, or None when it is missing."""
    if internals_lib is None:
        return None
    try:
        function = getattr(internals_lib, name)
    except AttributeError:
        logger.debug("The zen-internals library has no function %s", name)
        return None
    function.argtypes = argtypes
    function.restype = restype
    return function


_internals_lib = _load()

_detect_sql_injection = _bind(
    _internals_lib,
    "detect_sql_injection",
    [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_int,
    ],
    ctypes.c_int,
)


def detect_sql_injection(query: bytes, user_input: bytes, dialect: int) -> int:
    """
    Returns the library's result: 0 is no injection, 1 is an injection, 2 is an error
    and 3 means the query could not be tokenized. Returns 2 when the function is not loaded.
    """
    if _detect_sql_injection is None:
        return 2
    query_buffer = (ctypes.c_uint8 * len(query)).from_buffer_copy(query)
    user_input_buffer = (ctypes.c_uint8 * len(user_input)).from_buffer_copy(user_input)
    return _detect_sql_injection(
        query_buffer, len(query), user_input_buffer, len(user_input), dialect
    )
