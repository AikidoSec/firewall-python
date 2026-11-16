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
CHALLENGE = b"c" * 32
OTHER_CHALLENGE = b"d" * 32


def test_sealed_body_round_trips():
    assert unseal(KEY, REQUEST, CHALLENGE, seal(KEY, REQUEST, CHALLENGE, BODY)) == BODY


def test_other_key_is_rejected():
    with pytest.raises(InvalidSignature):
        unseal(b"other", REQUEST, CHALLENGE, seal(KEY, REQUEST, CHALLENGE, BODY))


def test_request_is_rejected_as_a_response():
    with pytest.raises(InvalidSignature):
        unseal(KEY, RESPONSE, CHALLENGE, seal(KEY, REQUEST, CHALLENGE, BODY))


def test_frame_signed_for_another_challenge_is_rejected():
    frame = seal(KEY, REQUEST, CHALLENGE, BODY)
    with pytest.raises(InvalidSignature):
        unseal(KEY, REQUEST, OTHER_CHALLENGE, frame)


def test_changed_body_is_rejected():
    frame = bytearray(seal(KEY, REQUEST, CHALLENGE, BODY))
    frame[-1] ^= 1
    with pytest.raises(InvalidSignature):
        unseal(KEY, REQUEST, CHALLENGE, bytes(frame))


def test_short_frame_is_rejected():
    with pytest.raises(InvalidSignature):
        unseal(KEY, REQUEST, CHALLENGE, b"short")


def test_short_challenge_is_rejected():
    with pytest.raises(InvalidSignature):
        unseal(KEY, REQUEST, b"short", seal(KEY, REQUEST, CHALLENGE, BODY))
