"""
Exports different types of Aikido Exception
"""


class AikidoException(Exception):
    """General AikidoException class"""


class AikidoSQLInjection(AikidoException):
    """Exception because of SQL Injection"""


class AikidoNoSQLInjection(AikidoException):
    """Exception because of NoSQL Injection"""


class AikidoRateLimiting(AikidoException):
    """Exception caused when a page was rate limited"""

    def __init__(self, message="You are rate limited by Aikido firewall."):
        super().__init__(message)
        self.message = message


class AikidoShellInjection(AikidoException):
    """Exception becausen of Shell Injection"""

    def __init__(self, message="Possible Shell Injection"):
        super().__init__(message)
        self.message = message


class AikidoPathTraversal(AikidoException):
    """Exception because of a path traversal"""

    def __init__(self, message="This is a path traversal attack, halted by Aikido."):
        super().__init__(self, message)
        self.message = message


class AikidoSSRF(AikidoException):
    """Exception because of SSRF"""
