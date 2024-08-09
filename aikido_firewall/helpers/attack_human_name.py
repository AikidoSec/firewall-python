"""Helper function file, see function docstring"""


def attack_human_name(kind):
    """Return the human name of each kind of attack"""
    if kind == "nosql_injection":
        return "a NoSQL injection"
    elif kind == "sql_injection":
        return "an SQL injection"
    elif kind == "shell_injection":
        return "a shell injection"
    elif kind == "path_traversal":
        return "a path traversal attack"
    elif kind == "ssrf":
        return "a server-side request forgery"
    else:
        return "unknown"
