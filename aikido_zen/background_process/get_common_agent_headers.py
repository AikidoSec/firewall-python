import aikido_zen.config as config
from aikido_zen.helpers.get_agent_session_id import get_agent_session_id
from aikido_zen.helpers.get_hostname import get_hostname
from aikido_zen.helpers.get_machine_ip import get_ip


def get_common_agent_headers():
    return {
        "X-Agent-Platform": "python",
        "X-Agent-Library": config.LIBRARY_NAME,
        "X-Agent-Version": config.PKG_VERSION,
        "X-Agent-Hostname": _header_value(get_hostname()),
        "X-Agent-IP-Address": _header_value(get_ip()),
        "X-Agent-Session-Id": get_agent_session_id(),
    }


def _header_value(value):
    # Header values are latin-1, and one that cannot be encoded fails the request.
    try:
        value.encode("latin-1")
    except UnicodeEncodeError:
        return "unknown"
    return value or "unknown"
