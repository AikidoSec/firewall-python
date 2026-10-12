import os
import time
import uuid


def uuid7():
    if hasattr(uuid, "uuid7"):
        return str(uuid.uuid7())
    return uuid7_polyfill()


def uuid7_polyfill():
    value = bytearray(os.urandom(16))
    timestamp_ms = time.time_ns() // 1_000_000
    value[0:6] = timestamp_ms.to_bytes(6, "big")
    value[6] = (value[6] & 0x0F) | 0x70  # version 7
    value[8] = (value[8] & 0x3F) | 0x80  # RFC 9562 variant
    return str(uuid.UUID(bytes=bytes(value)))
