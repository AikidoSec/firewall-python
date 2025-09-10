methods = {
    "BADMETHOD",
    "BADHTTPMETHOD",
    "BADDATA",
    "BADMTHD",
    "BDMTHD",
}


def is_web_scan_method(method: str) -> bool:
    return method.upper() in methods
