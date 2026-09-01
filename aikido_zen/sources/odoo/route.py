from uuid import UUID


_SAFE_ROUTE_ARGUMENT_TYPES = (str, int, float, bool)


def extract_route_arguments(arguments):
    if not hasattr(arguments, "items"):
        return {}

    result = {}
    for name, value in arguments.items():
        if value is None or type(value) in _SAFE_ROUTE_ARGUMENT_TYPES:
            result[name] = value
        elif isinstance(value, UUID):
            result[name] = str(value)
    return result
