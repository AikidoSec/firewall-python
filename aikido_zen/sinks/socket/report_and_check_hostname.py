from aikido_zen.context import get_current_context
from aikido_zen.errors import AikidoSSRF
from aikido_zen.sinks.socket.normalize_hostname import normalize_hostname
from aikido_zen.thread.thread_cache import get_cache


def report_and_check_hostname(hostname, port):
    cache = get_cache()
    if not cache:
        return

    hostname = normalize_hostname(hostname)
    cache.hostnames.add(hostname, port)

    context = get_current_context()
    is_bypassed = context and cache.is_bypassed_ip(context.remote_address)

    if cache.config and not is_bypassed:
        if cache.config.should_block_outgoing_request(hostname):
            raise AikidoSSRF(f"Zen has blocked an outbound connection to {hostname}")
