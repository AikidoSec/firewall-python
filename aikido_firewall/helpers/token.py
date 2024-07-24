"""
Helper module for token
"""

class Token:
    """Class that encapsulates the token"""

    def __init__(self, token):
        if not isinstance(token, str):
            raise ValueError("Token should be an instance of string")
        if len(token) == 0:
            raise ValueError("Token cannot be an empty string")
        self.token = token

    def __str__(self):
        return self.token

def get_token_from_env():
    """
    Fetches the token from the env variable ""
    """
    return Token("xyz")
