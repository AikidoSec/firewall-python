"""
Helper function file, see funtion definition
"""

from aikido_zen.helpers.try_decode_as_jwt import try_decode_as_jwt
from aikido_zen.helpers.is_mapping import is_mapping
from aikido_zen.helpers.build_path_to_payload import build_path_to_payload
import aikido_zen.context as ctx


def extract_strings_from_user_input_cached(obj, source):
    """Use the cache to speed up getting user input"""
    context = ctx.get_current_context()

    if not context:
        #  context may not exist in all situations, in that cases the cache should be skipped
        return extract_strings_from_user_input(obj)

    if context.parsed_userinput and context.parsed_userinput.get(source):
        return context.parsed_userinput.get(source)
    res = extract_strings_from_user_input(obj)

    context.parsed_userinput[source] = res
    context.set_as_current_context()
    return res


def extract_strings_from_user_input(obj, path_to_payload=None):
    """
    Extracts strings from an object (user input)
    """
    if path_to_payload is None:
        path_to_payload = []

    results = {}

    if is_mapping(obj):
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
                if k == "iss" or v.endswith("<jwt>.iss"):
                    # Do not add the issuer of the JWT as a string because it can contain a
                    # domain / url and produce false positives
                    continue
                results[k] = v

    return results
