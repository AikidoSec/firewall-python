"""Exports `process_route`"""


def process_route(reporter, data, conn, queue=None):
    """Called every time the user visits a route"""
    if reporter:
        reporter.routes.add_route(method=data[0], path=data[1])
