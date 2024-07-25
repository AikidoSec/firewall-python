"""
init.py file for the module to detect NoSQL Injections
"""

import json
from aikido_firewall.helpers.is_plain_object import is_plain_object
from aikido_firewall.helpers.build_path_to_payload import build_path_to_payload
from aikido_firewall.helpers.try_decode_as_jwt import try_decode_as_jwt
from aikido_firewall.context import UINPUT_SOURCES


def match_filter_part_in_user(user_input, filter_part, path_to_payload=[]):
    if isinstance(user_input, str):
        jwt = try_decode_as_jwt(user_input)
        if jwt[0]:
            return match_filter_part_in_user(
                jwt[1], filter_part, path_to_payload + [{"type": "jwt"}]
            )
    if user_input == filter_part:
        return {"match": True, "pathToPayload": build_path_to_payload(path_to_payload)}

    if is_plain_object(user_input):
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
    return {key: value for key, value in filter.items() if key.startswith("$")}


def find_filter_part_with_operators(user_input, part_of_filter):
    print("ui", json.dumps(part_of_filter))
    if is_plain_object(part_of_filter):
        print("Prev part of filter", part_of_filter)
        obj = remove_keys_that_dont_start_with_dollar_sign(part_of_filter)
        print("Object", obj)
        if len(obj) > 0:
            print("len > 0")
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


def detect_no_sql_injection(request, _filter):
    """
    Give a context object and a nosql filter and this function
    checks if there is a NoSQL injection
    """
    if not is_plain_object(_filter) and not isinstance(_filter, list):
        return {"injection": False}

    for source in UINPUT_SOURCES:
        if request.get(source):
            print("Getting source %s", source)
            print(request[source])
            result = find_filter_part_with_operators(request[source], _filter)

            if result.get("found"):
                return {
                    "injection": True,
                    "source": source,
                    "pathToPayload": result.get("pathToPayload"),
                    "payload": result.get("payload"),
                }

    return {"injection": False}
