"""
Exports different types of Aikido Exception
"""


class AikidoException(Exception):
    """General AikidoException class"""


class AikidoSQLInjection(AikidoException):
    """Exception because of SQL Injection"""


class AikidoNoSQLInjection(AikidoException):
    """Exception because of NoSQL Injection"""
