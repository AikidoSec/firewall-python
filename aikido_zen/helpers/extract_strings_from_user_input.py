"""
Helper function file, see funtion definition
"""

from aikido_zen.helpers.try_decode_as_jwt import try_decode_as_jwt
from aikido_zen.helpers.is_mapping import is_mapping
from aikido_zen.helpers.build_path_to_payload import build_path_to_payload
import aikido_zen.context as ctx

# Deeper input would overflow the stack and let the request through unchecked.
MAX_TRAVERSAL_DEPTH = 30


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

    results, _ = extract_strings_and_nesting(obj, path_to_payload)
    return results


def extract_strings_and_nesting(obj, path_to_payload):
    """Extracts strings from an object and returns how deep its containers nest"""
    results = {}

    if len(path_to_payload) >= MAX_TRAVERSAL_DEPTH:
        return results, MAX_TRAVERSAL_DEPTH + 1

    nesting = 0

    if is_mapping(obj):
        #  Stringifying the dict and adding it as user input is resource intensive
        #  And in most cases shouldn't be necessary.
        for key, value in obj.items():
            results[key] = build_path_to_payload(path_to_payload)
            child_results, child_nesting = extract_strings_and_nesting(
                value, path_to_payload + [{"type": "object", "key": key}]
            )
            for k, v in child_results.items():
                results[k] = v
            nesting = max(nesting, child_nesting + 1)

    if isinstance(obj, (set, list, tuple)):
        #  Add the stringified array as well to the results, there might
        #  be accidental concatenation if the client expects a string but gets the array
        #  E.g. HTTP Parameter pollution
        for i, value in enumerate(obj):
            child_results, child_nesting = extract_strings_and_nesting(
                value, path_to_payload + [{"type": "array", "index": i}]
            )
            for k, v in child_results.items():
                results[k] = v
            nesting = max(nesting, child_nesting + 1)

        #  We track how deep the children nest because str() walks the whole array by
        #  itself, ignoring our limit; too deep an array would raise a RecursionError.
        if nesting <= MAX_TRAVERSAL_DEPTH:
            results[str(obj)] = build_path_to_payload(path_to_payload)

    if isinstance(obj, str):
        results[obj] = build_path_to_payload(path_to_payload)
        jwt = try_decode_as_jwt(obj)
        if jwt[0]:
            child_results, _ = extract_strings_and_nesting(
                jwt[1], path_to_payload + [{"type": "jwt"}]
            )
            for k, v in child_results.items():
                if k == "iss" or v.endswith("<jwt>.iss"):
                    # Do not add the issuer of the JWT as a string because it can contain a
                    # domain / url and produce false positives
                    continue
                results[k] = v

    return results, nesting
