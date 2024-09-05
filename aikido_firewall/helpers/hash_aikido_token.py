"""Helper function file, see function docstring"""

import os
import hashlib


def hash_aikido_token():
    """Creates a hash of AIKIDO_TOKEN"""
    token = os.getenv("AIKIDO_TOKEN")

    if isinstance(token, str):
        hash_object = hashlib.sha256(token.encode("utf-8"))
        return hash_object.hexdigest()
    hash_object = hashlib.sha256("default".encode("utf-8"))
    return hash_object.hexdigest()
