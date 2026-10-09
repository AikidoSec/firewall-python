"""
Exports `extract_tool_calls_from_ai_response`
"""


def _get(obj, name):
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def extract_tool_calls_from_ai_response(response):
    """Extract (name, arguments) pairs from Completions or Responses payloads."""
    found = []
    if response is None:
        return found

    for choice in _get(response, "choices") or []:
        message = _get(choice, "message")
        if not message:
            continue
        for tool_call in _get(message, "tool_calls") or []:
            function = _get(tool_call, "function")
            if not function:
                continue
            name = _get(function, "name")
            if name:
                found.append((name, _get(function, "arguments")))

    for item in _get(response, "output") or []:
        if _get(item, "type") != "function_call":
            continue
        name = _get(item, "name")
        if name:
            found.append((name, _get(item, "arguments")))

    return found
