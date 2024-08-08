"""Exports `process_route`"""


def process_route(bg_process, data, conn):
    """Called every time the user visits a route"""
    if bg_process.reporter:
        bg_process.reporter.routes.add_route(method=data[0], path=data[1])
