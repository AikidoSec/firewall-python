from aikido_zen.thread.thread_cache import get_cache


def should_block_outbound_domain(hostname, port):
    process_cache = get_cache()
    if not process_cache:
        return False

    # We store the hostname before checking the blocking status
    # This is because if we are in lockdown mode and blocking all new hostnames, it should still
    # show up in the dashboard. This allows the user to allow traffic to newly detected hostnames.
    process_cache.hostnames.add(hostname, port)

    return process_cache.config.should_block_outgoing_request(hostname)
