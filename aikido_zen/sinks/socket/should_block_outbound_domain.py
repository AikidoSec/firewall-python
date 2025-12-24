from aikido_zen.context import get_current_context
from aikido_zen.errors import AikidoSSRF
from aikido_zen.sinks.socket.normalize_hostname import normalize_hostname
from aikido_zen.thread.thread_cache import get_cache


def should_block_outbound_domain(hostname, port):
    process_cache = get_cache()
    if not process_cache:
        return False
    process_cache.hostnames.add(hostname, port)

    return process_cache.config.should_block_outgoing_request(hostname)
