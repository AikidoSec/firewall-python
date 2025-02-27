from aikido_zen.context import Context


def on_init_request(context: Context):
    """
    This function gets the newly created context object and does the following :
    - Renews thread cache if necessary
    - Sets context object
    - Checks if the IP is allowed to access the route (route-specific)
    - Checks if the IP is in an allowlist (if that exists)
    - Checks if the IP is in a blocklist (if that exists)
    - Checks if the user agent is blocked (if the regex exists)
    """
    pass
