"""Exports `process_force_protection_off`"""


def process_force_protection_off(bg_process, data, conn):
    """Returns a value, if the protection should be forced of or not"""
    match = bg_process.reporter.conf.get_endpoint(data[1])
    conn.send(match and match["endpoint"]["forceProtectionOff"])
