"""
File for attack-related functions, (e.g. attack_get_human_name)
"""


def attack_get_human_name(kind):
    """Return a human-readable name for the given attack kind."""
    attack_names = {
        "nosql_injection": "a NoSQL injection",
        "sql_injection": "an SQL injection",
        "shell_injection": "a shell injection",
        "path_traversal": "a path traversal attack",
        "ssrf": "a server-side request forgery",
    }

    return attack_names.get(kind, "Unknown attack kind")
