from aikido_zen.sinks import on_import


@on_import("openai")
def patch(m):
    """patching module openai"""
    pass
