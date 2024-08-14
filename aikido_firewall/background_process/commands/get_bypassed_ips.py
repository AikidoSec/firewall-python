"""Mainly exports `process_get_bypassed_ips`"""


def process_get_bypassed_ips(bg_process, data, conn):
    """Checks if the ip is on the bypass list"""
    bypassed_ips = bg_process.reporter.conf.bypassed_ips
    conn.send(bypassed_ips)
