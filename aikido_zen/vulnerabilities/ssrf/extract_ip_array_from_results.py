"""Exports function extract_ip_array_from_results"""


def extract_ip_array_from_results(dns_results):
    """Extracts IP's from dns results"""
    ip_addresses = []
    for result in dns_results:
        ip_object = result[4]
        if ip_object is not None and ip_object[0] is not None:
            ip_addresses.append(ip_object[0])
    return ip_addresses
