web_scan_methods = {
    "BADMETHOD",
    "BADHTTPMETHOD",
    "BADDATA",
    "BADMTHD",
    "BDMTHD",
}


def is_web_scan_method(method: str) -> bool:
    return method.upper() in web_scan_methods
