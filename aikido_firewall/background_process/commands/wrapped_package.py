"""Exports `process_wrapped_package`"""


def process_wrapped_package(bg_process, data, conn):
    """A package has been wrapped"""
    if bg_process.reporter:
        pkg_name = data["name"]
        pkg_details = data["details"]
        bg_process.reporter.packages[pkg_name] = pkg_details
        conn.send(True)
    else:
        conn.send(False)
