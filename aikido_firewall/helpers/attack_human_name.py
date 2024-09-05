"""Helper function file, see function docstring"""


def attack_human_name(kind):
    """Return the human name of each kind of attack"""
    if kind == "nosql_injection":
        return "a NoSQL injection"
    if kind == "sql_injection":
        return "an SQL injection"
    if kind == "shell_injection":
        return "a shell injection"
    if kind == "path_traversal":
        return "a path traversal attack"
    if kind == "ssrf":
        return "a server-side request forgery"
    return "unknown"
