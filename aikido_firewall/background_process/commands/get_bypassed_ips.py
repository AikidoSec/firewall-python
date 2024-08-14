"""Mainly exports `process_get_bypassed_ips`"""


def process_get_bypassed_ips(bg_process, data, conn):
    """
    Gets all the bypassed ip's from the ServiceConfig object, and
    sends them over IPC (bypassed_ips is a set, not a list)
    """
    bypassed_ips = bg_process.reporter.conf.bypassed_ips
    conn.send(bypassed_ips)
