"""
Helper function file, see funtion definition
"""


def build_path_to_payload(path_to_payload):
    """
    Create a string so people see the path to where
    the injection took place
    """
    if len(path_to_payload) == 0:
        return "."

    result = ""
    for part in path_to_payload:
        if part["type"] == "object":
            result += "." + part["key"]
        elif part["type"] == "array":
            result += f".[{part['index']}]"
        elif part["type"] == "jwt":
            result += "<jwt>"

    return result
