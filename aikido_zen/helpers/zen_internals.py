"""
Python bindings for the zen-internals Rust library. The library is loaded once, when
this module is imported, and every feature that uses it goes through these functions.
"""

import ctypes
import os
import platform
import sysconfig
from array import array
from itertools import accumulate, islice

from aikido_zen.helpers.logging import logger


_TARGET = f"{platform.system().lower()}-{platform.machine().lower()}"


def _binary_path():
    os_name = platform.system().lower()
    machine = platform.machine().lower()
    is_arm = "arm64" in machine or "aarch64" in machine
    file_name = "libzen_internals_"

    # On macOS, platform.machine() returns "arm64" for Apple Silicon
    # On Linux, platform.machine() returns "aarch64" for ARM64
    if is_arm:
        file_name += "aarch64-"
    # On macOS, platform.machine() returns "x86_64" for Intel
    # On Linux, platform.machine() returns "x86_64" for AMD64
    elif "x86_64" in machine or "amd64" in machine:
        file_name += "x86_64-"

    if os_name == "windows":
        file_name += "pc-windows-msvc.dll" if is_arm else "pc-windows-gnu.dll"
    elif os_name == "darwin":
        file_name += "apple-darwin.dylib"
    elif os_name in ["linux", "linux2"]:
        # The library must use the same libc as this Python, which records it at build
        # time (for example "x86_64-pc-linux-musl"). platform.libc_ver() and files under
        # /lib describe the system, which can have both glibc and musl installed.
        host = sysconfig.get_config_var("HOST_GNU_TYPE") or ""
        libc = "musl" if "musl" in host else "gnu"
        file_name += f"unknown-linux-{libc}.so"

    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../libs", file_name
    )


def _load():
    """Returns the loaded library and None, or None and the reason it did not load."""
    binary_path = _binary_path()
    if not os.path.exists(binary_path):
        return None, (
            f"Cannot find the zen-internals library for {_TARGET}. "
            "Request support: https://github.com/AikidoSec/firewall-python/issues"
        )
    try:
        return ctypes.CDLL(binary_path), None
    except OSError as e:
        return None, f"Failed to load the zen-internals library for {_TARGET}: {e}"


def _warn_unavailable(consequence, function_name):
    reason = _load_error or (
        f"The zen-internals library for {_TARGET} has no {function_name} function."
    )
    logger.warning("%s. %s", consequence, reason)


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


_internals_lib, _load_error = _load()

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
if _detect_sql_injection is None:
    _warn_unavailable(
        "Zen will NOT block SQL injection attacks", "detect_sql_injection"
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


class _ByteSlice(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_char_p), ("len", ctypes.c_size_t)]


_ip_matcher_create = _bind(
    _internals_lib,
    "ip_matcher_create",
    [ctypes.POINTER(_ByteSlice), ctypes.c_size_t],
    ctypes.c_void_p,
)
_ip_matcher_has = _bind(
    _internals_lib,
    "ip_matcher_has",
    [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t],
    ctypes.c_int,
)
_ip_matcher_free = _bind(_internals_lib, "ip_matcher_free", [ctypes.c_void_p], None)


def has_ip_matcher() -> bool:
    return None not in (_ip_matcher_create, _ip_matcher_has, _ip_matcher_free)


if not has_ip_matcher():
    _warn_unavailable(
        "Zen will NOT apply IP lists or block SSRF attacks", "ip_matcher_create"
    )


def ip_matcher_create(networks: list):
    """Returns the matcher handle, or None when the library cannot build one."""
    if _ip_matcher_create is None:
        return None
    count = len(networks)
    if not count:
        return _ip_matcher_create(None, 0) or None

    # One ctypes object per network holds the GIL for the whole loop, so the thread that
    # answers CHECK_FIREWALL_LISTS misses its 10 ms timeout during a rebuild. One buffer
    # and a flat array of (pointer, length) pairs keep the Python part short.
    lengths = array("Q", map(len, networks))
    buffer = ctypes.create_string_buffer(b"".join(networks), sum(lengths))
    offsets = islice(accumulate(lengths, initial=0), count)
    pairs = array("Q", bytes(ctypes.sizeof(_ByteSlice) * count))
    pairs[0::2] = array("Q", map(ctypes.addressof(buffer).__add__, offsets))
    pairs[1::2] = lengths
    descriptors = (_ByteSlice * count).from_buffer(pairs)
    return _ip_matcher_create(descriptors, count) or None


def ip_matcher_has(handle, network: bytes) -> bool:
    return _ip_matcher_has(handle, network, len(network)) == 1


def ip_matcher_free(handle) -> None:
    _ip_matcher_free(handle)
