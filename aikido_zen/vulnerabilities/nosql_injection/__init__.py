"""
init.py file for the module to detect NoSQL Injections
"""

import json
from aikido_zen.helpers.is_mapping import is_mapping
from aikido_zen.helpers.build_path_to_payload import build_path_to_payload
from aikido_zen.helpers.try_decode_as_jwt import try_decode_as_jwt
from aikido_zen.context import UINPUT_SOURCES


def match_filter_part_in_user(user_input, filter_part, path_to_payload=None):
    """
    This tries to match a filter part to a part in user input
    """
    if not path_to_payload:
        path_to_payload = []
    if isinstance(user_input, str):
        jwt = try_decode_as_jwt(user_input)
        if jwt[0]:
            return match_filter_part_in_user(
                jwt[1], filter_part, path_to_payload + [{"type": "jwt"}]
            )

    if is_mapping(user_input):
        filtered_input = remove_keys_that_dont_start_with_dollar_sign(user_input)
        if filtered_input == filter_part:
            return {
                "match": True,
                "pathToPayload": build_path_to_payload(path_to_payload),
            }
        for key in user_input:
            match = match_filter_part_in_user(
                user_input[key],
                filter_part,
                path_to_payload + [{"type": "object", "key": key}],
            )
            if match.get("match"):
                return match
    if isinstance(user_input, list):
        for index, value in enumerate(user_input):
            match = match_filter_part_in_user(
                value,
                filter_part,
                path_to_payload + [{"type": "array", "index": index}],
            )
            if match.get("match"):
                return match

    return {"match": False}


def remove_keys_that_dont_start_with_dollar_sign(filter):
    """
    This removes key that don't start with $, since they are not dangerous
    """
    return {key: value for key, value in filter.items() if key.startswith("$")}


def find_filter_part_with_operators(user_input, part_of_filter):
    """
    This looks for parts in the filter that have NSQL operators (e.g. $)
    """
    if is_mapping(part_of_filter):
        obj = remove_keys_that_dont_start_with_dollar_sign(part_of_filter)
        if len(obj) > 0:
            result = match_filter_part_in_user(user_input, obj)

            if result.get("match"):
                return {
                    "found": True,
                    "pathToPayload": result.get("pathToPayload"),
                    "payload": obj,
                }
        for key in part_of_filter:
            result = find_filter_part_with_operators(user_input, part_of_filter[key])

            if result.get("found"):
                return {
                    "found": True,
                    "pathToPayload": result.get("pathToPayload"),
                    "payload": result.get("payload"),
                }

    if isinstance(part_of_filter, list):
        for val in part_of_filter:
            result = find_filter_part_with_operators(user_input, val)
            if result.get("found"):
                return {
                    "found": True,
                    "pathToPayload": result.get("pathToPayload"),
                    "payload": result.get("payload"),
                }

    return {"found": False}


def detect_nosql_injection(request, _filter):
    """
    Give a context object and a nosql filter and this function
    checks if there is a NoSQL injection
    """
    if not is_mapping(_filter) and not isinstance(_filter, list):
        return {}

    for source in UINPUT_SOURCES:
        if hasattr(request, source):
            result = find_filter_part_with_operators(getattr(request, source), _filter)

            if result.get("found"):
                return {
                    "injection": True,
                    "source": source,
                    "pathToPayload": result.get("pathToPayload"),
                    "payload": result.get("payload"),
                }

    return {}
