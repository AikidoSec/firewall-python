"""
Python bindings for the zen-internals Rust library. The library is loaded once, when
this module is imported, and every feature that uses it goes through these functions.
"""

import ctypes
import os
import platform
import sysconfig

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
    binary_path = _binary_path()
    if not os.path.exists(binary_path):
        logger.warning(
            "Cannot find the zen-internals library for %s. "
            "Request support: https://github.com/AikidoSec/firewall-python/issues",
            _TARGET,
        )
        return None
    try:
        return ctypes.CDLL(binary_path)
    except OSError as e:
        error = e
    # A musl Python built without HOST_GNU_TYPE picks the glibc build, which musl
    # cannot load.
    musl_path = os.path.join(
        os.path.dirname(binary_path),
        os.path.basename(binary_path).replace("-gnu.so", "-musl.so"),
    )
    if musl_path != binary_path and os.path.exists(musl_path):
        try:
            return ctypes.CDLL(musl_path)
        except OSError:
            pass
    logger.warning(
        "Failed to load the zen-internals library for %s: %s", _TARGET, error
    )
    return None


def _bind(internals_lib, name, argtypes, restype):
    """Returns the library function with its C types set, or None when it is missing."""
    if internals_lib is None:
        return None
    try:
        function = getattr(internals_lib, name)
    except AttributeError:
        logger.warning(
            "The zen-internals library for %s has no %s function.", _TARGET, name
        )
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
if _detect_sql_injection is None:
    logger.warning("Zen will NOT block SQL injection attacks.")


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


_ip_matcher_create = _bind(
    _internals_lib,
    "ip_matcher_create",
    [ctypes.c_char_p, ctypes.c_size_t],
    ctypes.c_void_p,
)
_ip_matcher_has = _bind(
    _internals_lib,
    "ip_matcher_has",
    [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t],
    ctypes.c_int,
)
_ip_matcher_free = _bind(_internals_lib, "ip_matcher_free", [ctypes.c_void_p], None)
_ip_matcher_rejected_count = _bind(
    _internals_lib, "ip_matcher_rejected_count", [ctypes.c_void_p], ctypes.c_size_t
)


def has_ip_matcher() -> bool:
    return None not in (_ip_matcher_create, _ip_matcher_has, _ip_matcher_free)


if not has_ip_matcher():
    logger.warning("Zen will NOT apply IP lists or block SSRF attacks.")


def ip_matcher_create(networks: bytes):
    """Builds a matcher from newline-separated networks. Returns None on failure."""
    # A handle is only useful when has and free exist too, so ip_matcher_has and
    # ip_matcher_free never need their own check.
    if not has_ip_matcher():
        return None
    return _ip_matcher_create(networks, len(networks))


def ip_matcher_has(handle, network: bytes) -> bool:
    return _ip_matcher_has(handle, network, len(network)) == 1


def ip_matcher_free(handle) -> None:
    _ip_matcher_free(handle)


def ip_matcher_rejected_count(handle) -> int:
    """Returns how many networks the library could not parse, or 0 when not loaded."""
    if _ip_matcher_rejected_count is None:
        return 0
    return _ip_matcher_rejected_count(handle)
