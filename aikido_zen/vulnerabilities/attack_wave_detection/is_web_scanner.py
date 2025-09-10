from aikido_zen.context import Context
from aikido_zen.vulnerabilities.attack_wave_detection.is_web_scan_method import (
    is_web_scan_method,
)
from aikido_zen.vulnerabilities.attack_wave_detection.is_web_scan_path import (
    is_web_scan_path,
)
from aikido_zen.vulnerabilities.attack_wave_detection.query_params_contain_dangerous_strings import (
    query_params_contain_dangerous_strings,
)


# Assume Context is a dictionary or a class with the required attributes
def is_web_scanner(context: Context) -> bool:
    if context.method and is_web_scan_method(context.method):
        return True
    if context.route and is_web_scan_path(context.route):
        return True
    if query_params_contain_dangerous_strings(context):
        return True
    return False
