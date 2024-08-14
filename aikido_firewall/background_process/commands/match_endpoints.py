"""Exports `process_match_endpoints`"""


def process_match_endpoints(bg_process, data, conn):
    """
    Returns all the matches found in the endpoints list for the given context,
    data: compressed_context
    """
    matches = bg_process.reporter.conf.get_endpoints(data)
    conn.send(matches)
