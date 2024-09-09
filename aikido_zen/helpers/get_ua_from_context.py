def get_ua_from_context(context):
    """Tries to retrieve the user agent from context"""
    for k, v in context.headers.items():
        if k.lower() == "user-agent":
            return v
    return None
