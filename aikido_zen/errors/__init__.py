"""
Exports different types of Aikido Exception
"""

from aikido_zen.helpers.attack_human_name import attack_human_name


def generate_default_message(kind):
    """Generates a default message based on kind of attack"""
    return "Zen has blocked " + attack_human_name(kind)


class AikidoException(Exception):
    """General AikidoException class"""

    kind = None

    def __init__(self, message=None):
        if isinstance(message, str):
            super().__init__(self, message)
        else:
            super().__init__(self, generate_default_message(self.kind))


class AikidoSQLInjection(AikidoException):
    """Exception because of SQL Injection"""

    def __init__(self, dialect="unknown"):
        super().__init__(
            generate_default_message("sql_injection") + ", dialect: " + dialect
        )


class AikidoNoSQLInjection(AikidoException):
    """Exception because of NoSQL Injection"""

    kind = "nosql_injection"


class AikidoRateLimiting(AikidoException):
    """Exception caused when a page was rate limited"""

    def __init__(self, message="You are rate limited by Zen."):
        super().__init__(message)
        self.message = message


class AikidoShellInjection(AikidoException):
    """Exception becausen of Shell Injection"""

    kind = "shell_injection"


class AikidoPathTraversal(AikidoException):
    """Exception because of a path traversal"""

    kind = "path_traversal"


class AikidoSSRF(AikidoException):
    """Exception because of SSRF"""

    kind = "ssrf"
