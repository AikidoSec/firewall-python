"""
The possible SQL Dialects (Characters that vary based on the language)
e.g. postgres dialect
"""

from abc import ABC, abstractmethod


class SQLDialect(ABC):
    """
    A subclass that provides a template to work with
    """

    @abstractmethod
    def get_dangerous_strings(self):
        """
        Use this to add dangerous strings that are specific to the SQL dialect
        These are matched without surrounding spaces,
        so if you add "SELECT" it will match "SELECT" and "SELECTED"
        """

    @abstractmethod
    def get_keywords(self):
        """
        Use this to add keywords that are specific to the SQL dialect
        These are matched with surrounding spaces,
        so if you add "SELECT" it will match "SELECT" but not "SELECTED"
        """
