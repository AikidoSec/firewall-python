"""
Exports different types of Aikido Exception
"""


class AikidoException(Exception):
    """General AikidoException class"""


class AikidoSQLInjection(AikidoException):
    """Exception because of SQL Injection"""


class AikidoNoSQLInjection(AikidoException):
    """Exception because of NoSQL Injection"""


class AikidoPathTraversal(AikidoException):
    """Exception because of a path traversal"""

    def __init__(self, message="This is a path traversal attack, halted by Aikido."):
        super().__init__(self, message)
        self.message = message
