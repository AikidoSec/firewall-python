import hashlib
import hmac

MAC_SIZE = hashlib.sha256().digest_size
REQUEST = b"request"
RESPONSE = b"response"


class InvalidSignature(Exception):
    pass


def seal(key, label, body):
    return hmac.new(key, label + body, hashlib.sha256).digest() + body


def unseal(key, label, frame):
    if len(frame) < MAC_SIZE:
        raise InvalidSignature
    mac, body = frame[:MAC_SIZE], frame[MAC_SIZE:]
    expected = hmac.new(key, label + body, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected):
        raise InvalidSignature
    return body


class ReplyConnection:
    def __init__(self, connection, key):
        self._connection = connection
        self._key = key

    def send_bytes(self, body):
        self._connection.send_bytes(seal(self._key, RESPONSE, body))
