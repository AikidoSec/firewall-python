"""
Thread-safe singleton interface for the zen-internals Rust shared library.
Provides a ZenInternal class whose instances are all the same object (singleton),
so the DLL is searched for and dlopen'd exactly once.
"""

import ctypes
import json
import threading
from .get_lib_path import get_binary_path
from .map_dialect_to_rust_int import DIALECTS
from aikido_zen.helpers.encode_safely import encode_safely


class _Singleton(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ZenInternal(metaclass=_Singleton):
    """
    Thread-safe singleton wrapping the zen-internals Rust shared library.
    Sets up all FFI function signatures once on first instantiation.
    """

    def __init__(self):
        lib = ctypes.CDLL(get_binary_path())

        lib.detect_sql_injection.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_int,
        ]
        lib.detect_sql_injection.restype = ctypes.c_int

        lib.idor_analyze_sql_ffi.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_int,
        ]
        lib.idor_analyze_sql_ffi.restype = ctypes.c_void_p

        lib.free_string.argtypes = [ctypes.c_void_p]
        lib.free_string.restype = None

        self._lib = lib

    def detect_sql_injection(self, query, user_input, dialect):
        """Returns 1 (injection), 2 (error), 3 (tokenize fail), or 0 (clean)."""
        query_bytes = encode_safely(query)
        userinput_bytes = encode_safely(user_input)
        query_buffer = (ctypes.c_uint8 * len(query_bytes)).from_buffer_copy(query_bytes)
        userinput_buffer = (ctypes.c_uint8 * len(userinput_bytes)).from_buffer_copy(
            userinput_bytes
        )
        dialect_int = DIALECTS[dialect]
        return self._lib.detect_sql_injection(
            query_buffer,
            len(query_bytes),
            userinput_buffer,
            len(userinput_bytes),
            dialect_int,
        )

    def idor_analyze_sql(self, query, dialect):
        """
        Parses a SQL query and returns a list of statement dicts,
        an error dict, or None if the pointer was null.
        """
        query_bytes = encode_safely(query)
        query_buffer = (ctypes.c_uint8 * len(query_bytes)).from_buffer_copy(query_bytes)
        dialect_int = DIALECTS[dialect]

        result_ptr = self._lib.idor_analyze_sql_ffi(
            query_buffer,
            len(query_bytes),
            dialect_int,
        )

        if not result_ptr:
            return None

        result_str = ctypes.string_at(result_ptr).decode("utf-8")
        self._lib.free_string(result_ptr)
        return json.loads(result_str)
