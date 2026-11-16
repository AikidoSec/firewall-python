import pytest

from aikido_zen.background_process.message_auth import (
    REQUEST,
    RESPONSE,
    InvalidSignature,
    seal,
    unseal,
)

KEY = b"fixture"
BODY = b'["PING", []]'


def test_sealed_body_round_trips():
    assert unseal(KEY, REQUEST, seal(KEY, REQUEST, BODY)) == BODY


def test_other_key_is_rejected():
    with pytest.raises(InvalidSignature):
        unseal(b"other", REQUEST, seal(KEY, REQUEST, BODY))


def test_request_is_rejected_as_a_response():
    with pytest.raises(InvalidSignature):
        unseal(KEY, RESPONSE, seal(KEY, REQUEST, BODY))


def test_changed_body_is_rejected():
    frame = bytearray(seal(KEY, REQUEST, BODY))
    frame[-1] ^= 1
    with pytest.raises(InvalidSignature):
        unseal(KEY, REQUEST, bytes(frame))


def test_short_frame_is_rejected():
    with pytest.raises(InvalidSignature):
        unseal(KEY, REQUEST, b"short")
