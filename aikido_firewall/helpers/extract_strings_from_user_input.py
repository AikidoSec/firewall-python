"""
Helper function file, see funtion definition
"""

from aikido_firewall.helpers.try_decode_as_jwt import try_decode_as_jwt
from aikido_firewall.helpers.build_path_to_payload import build_path_to_payload
from aikido_firewall.context import get_current_context


def extract_strings_from_user_input_cached(obj, source):
    """Use the cache to speed up getting user input"""
    context = get_current_context()
    if context.parsed_userinput and context.parsed_userinput.get(source):
        return context.parsed_userinput.get(source)
    res = extract_strings_from_user_input(obj)

    context.parsed_userinput[source] = res
    context.set_as_current_context()
    return res


def reset_userinput_cache_for_given_source(source):
    """Resets cache for the given source"""
    context = get_current_context()
    if context.parsed_userinput and context.parsed_userinput.get(source):
        context.parsed_userinput[source] = None  # Empty cache


def extract_strings_from_user_input(obj, path_to_payload=None):
    """
    Extracts strings from an object (user input)
    """
    if path_to_payload is None:
        path_to_payload = []

    results = {}

    if isinstance(obj, dict):
        #  Stringifying the dict and adding it as user input is resource intensive
        #  And in most cases shouldn't be necessary.
        for key, value in obj.items():
            results[key] = build_path_to_payload(path_to_payload)
            for k, v in extract_strings_from_user_input(
                value, path_to_payload + [{"type": "object", "key": key}]
            ).items():
                results[k] = v

    if isinstance(obj, (set, list, tuple)):
        #  Add the stringified array as well to the results, there might
        #  be accidental concatenation if the client expects a string but gets the array
        #  E.g. HTTP Parameter pollution
        results[str(obj)] = build_path_to_payload(path_to_payload)
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
