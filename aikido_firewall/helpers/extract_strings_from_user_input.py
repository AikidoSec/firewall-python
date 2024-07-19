"""
Helper function file, see funtion definition
"""

from aikido_firewall.helpers.try_decode_as_jwt import try_decode_as_jwt
from aikido_firewall.helpers.build_path_to_payload import build_path_to_payload


def extract_strings_from_user_input(obj, path_to_payload=None):
    """
    Extracts strings from an object (user input)
    """
    if path_to_payload is None:
        path_to_payload = []

    results = {}

    if isinstance(obj, dict):
        for key, value in obj.items():
            results[key] = build_path_to_payload(path_to_payload)
            for k, v in extract_strings_from_user_input(
                value, path_to_payload + [{"type": "object", "key": key}]
            ).items():
                results[k] = v

    if isinstance(obj, list):
        for i, value in enumerate(obj):
            for k, v in extract_strings_from_user_input(
                value, path_to_payload + [{"type": "array", "index": i}]
            ).items():
                results[k] = v

    if isinstance(obj, str):
        results[obj] = build_path_to_payload(path_to_payload)
        jwt = try_decode_as_jwt(obj)
        if jwt[0]:
            for k, v in extract_strings_from_user_input(
                jwt[1], path_to_payload + [{"type": "jwt"}]
            ).items():
                results[k] = v

    return results
