"""
Exports different types of Aikido Exception
"""


class AikidoException(Exception):
    """General AikidoException class"""


class AikidoSQLInjection(AikidoException):
    """Exception because of SQL Injection"""


class AikidoNoSQLInjection(AikidoException):
    """Exception because of NoSQL Injection"""


class AikidoShellInjection(AikidoException):
    """Exception becausen of Shell Injection"""

    def __init__(self, message="Possible Shell Injection"):
        super().__init__(message)
        self.message = message
