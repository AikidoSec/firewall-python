import aikido_zen.config as config
from aikido_zen.helpers.get_agent_session_id import get_agent_session_id
from aikido_zen.helpers.get_hostname import get_hostname
from aikido_zen.helpers.get_machine_ip import get_ip

_UNKNOWN = "unknown"
_UNRESOLVED_IP = "x.x.x.x"  # What get_ip returns when it cannot resolve the address.


def get_common_agent_headers():
    ip_address = get_ip()
    return {
        "X-Agent-Platform": "python",
        "X-Agent-Version": config.PKG_VERSION,
        "X-Agent-Hostname": get_hostname() or _UNKNOWN,
        "X-Agent-IP-Address": _UNKNOWN if ip_address == _UNRESOLVED_IP else ip_address,
        "X-Agent-Session-Id": get_agent_session_id(),
    }
