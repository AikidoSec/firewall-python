def encode_safely(string: str) -> bytes:
    """Encodes the given string using UTF-8 encoding, and replaces encoding errors with �"""
    return string.encode("utf-8", errors="replace")
