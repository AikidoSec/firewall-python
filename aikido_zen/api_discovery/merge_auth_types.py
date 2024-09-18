"""Mainly exports merge_auth_types"""


def merge_auth_types(existing, new_auth):
    """
    Merge two auth type lists into one, without duplicates. (See get_auth_types)
    Can return None if both parameters are not a list.
    """
    if not isinstance(new_auth, list) or len(new_auth) == 0:
        return existing

    if not isinstance(existing, list) or len(existing) == 0:
        return new_auth

    result = existing.copy()

    for auth in new_auth:
        if not any(is_equal_api_auth_type(a, auth) for a in result):
            result.append(auth)

    return result


def is_equal_api_auth_type(a, b):
    """
    Compare two APIAuthType objects for equality.
    """
    return (
        a.get("type") == b.get("type")
        and a.get("in") == b.get("in")
        and a.get("name") == b.get("name")
        and a.get("scheme") == b.get("scheme")
    )
