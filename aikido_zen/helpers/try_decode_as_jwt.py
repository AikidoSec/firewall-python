"""
Helper function file, see function docstrin
"""

import base64
import json


def try_decode_as_jwt(jwt):
    """
    This will try to decode a string as a JWT
    """
    if "." not in jwt:
        return (False, None)

    parts = jwt.split(".")

    if len(parts) != 3:
        return (False, None)

    try:
        base64_decoded = base64.urlsafe_b64decode(str.encode(parts[1]) + b"==")
        jwt = json.loads(base64_decoded.decode("utf-8"))
        return (True, jwt)
    except Exception:
        return (False, None)
