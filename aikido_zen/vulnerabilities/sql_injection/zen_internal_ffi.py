"""
Interface for calling zen-internal shared library
"""

import ctypes
import threading
from .get_lib_path import get_binary_path
from ...helpers.encode_safely import encode_safely


class __Singleton(type):
    _instances = {}
    _lock = threading.Lock()  # Ensures thread safety

    def __call__(cls, *args, **kwargs):
        with cls._lock:  # Lock to make the check-and-create operation atomic
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ZenInternal(metaclass=__Singleton):
    # Reference : [rust lib]/src/sql_injection/helpers/select_dialect_based_on_enum.rs
    SQL_DIALECTS = {
        "generic": 0,
        "clickhouse": 3,
        "mysql": 8,
        "postgres": 9,
        "sqlite": 12,
    }

    def __init__(self):
        self._lib = ctypes.CDLL(get_binary_path())
        self._lib.detect_sql_injection.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_int,
        ]
        self._lib.detect_sql_injection.restype = ctypes.c_int

    def detect_sql_injection(self, query, user_input, dialect):
        query_bytes = encode_safely(query)
        userinput_bytes = encode_safely(user_input)
        query_buffer = (ctypes.c_uint8 * len(query_bytes)).from_buffer_copy(query_bytes)
        userinput_buffer = (ctypes.c_uint8 * len(userinput_bytes)).from_buffer_copy(
            userinput_bytes
        )
        dialect_int = self.SQL_DIALECTS[dialect]
        return self._lib.detect_sql_injection(
            query_buffer,
            len(query_bytes),
            userinput_buffer,
            len(userinput_bytes),
            dialect_int,
        )
