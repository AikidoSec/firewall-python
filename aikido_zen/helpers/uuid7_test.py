import re
import time

from aikido_zen.helpers.uuid7 import uuid7, uuid7_polyfill

_UUID_V7 = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)


def _timestamp_ms(value):
    return int(value.replace("-", "")[:12], 16)


def _assert_uuid7(generate):
    before = time.time_ns() // 1_000_000
    value = generate()
    after = time.time_ns() // 1_000_000

    assert _UUID_V7.fullmatch(value)
    assert before <= _timestamp_ms(value) <= after
    assert generate() != value


def test_uuid7_is_version_7():
    _assert_uuid7(uuid7)


def test_uuid7_polyfill_is_version_7():
    _assert_uuid7(uuid7_polyfill)
