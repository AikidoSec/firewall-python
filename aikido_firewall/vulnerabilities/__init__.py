"""
Exports `run_vulnerability_scan` function
"""

import json
from aikido_firewall.context import get_current_context
from aikido_firewall.errors import (
    AikidoException,
    AikidoSQLInjection,
    AikidoNoSQLInjection,
    AikidoShellInjection,
    AikidoPathTraversal,
    AikidoSSRF,
)
from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.get_clean_stacktrace import get_clean_stacktrace
from aikido_firewall.helpers.blocking_enabled import is_blocking_enabled
from .sql_injection.context_contains_sql_injection import context_contains_sql_injection
from .nosql_injection.check_context import check_context_for_nosql_injection
from .ssrf.check_context_for_ssrf import check_context_for_ssrf
from .shell_injection.check_context_for_shell_injection import (
    check_context_for_shell_injection,
)
from .path_traversal.check_context_for_path_traversal import (
    check_context_for_path_traversal,
)
from aikido_firewall.background_process.ipc_lifecycle_cache import get_cache


def run_vulnerability_scan(kind, op, args):
    """
    Generally checks context for the provided "kind" of injection,
    raises error if blocking is enabled, communicates it with connection_manager
    """
    context = get_current_context()
    comms = get_comms()
    lifecycle_cache = get_cache()
    if not context or not comms or not lifecycle_cache:
        logger.debug("Not running a vulnerability scan due to incomplete data.")
        logger.debug("%s : %s", kind, op)
        return

    if lifecycle_cache.protection_forced_off():
        #  The client turned protection off for this route, not scanning
        return
    if lifecycle_cache.is_bypassed_ip(context.remote_address):
        #  This IP is on the bypass list, not scanning
        return

    error_type = AikidoException  # Default error
    error_args = tuple()
    injection_results = {}

    if kind == "sql_injection":
        injection_results = context_contains_sql_injection(
            sql=args[0], dialect=args[1], operation=op, context=context
        )
        error_type = AikidoSQLInjection
        error_args = (type(args[1]).__name__,)  # Pass along the dialect
    elif kind == "nosql_injection":
        injection_results = check_context_for_nosql_injection(
            context=context, op=op, _filter=args[0]
        )
        error_type = AikidoNoSQLInjection
    elif kind == "shell_injection":
        injection_results = check_context_for_shell_injection(
            command=args[0], operation=op, context=context
        )
        error_type = AikidoShellInjection
    elif kind == "path_traversal":
        injection_results = check_context_for_path_traversal(
            filename=args[0], operation=op, context=context
        )
        error_type = AikidoPathTraversal
    elif kind == "ssrf":
        # Report hostname and port to background process :
        injection_results = check_context_for_ssrf(
            hostname=args[0], port=args[1], operation=op, context=context
        )
        error_type = AikidoSSRF
        blocked_request = is_blocking_enabled() and injection_results
        if not blocked_request:
            get_comms().send_data_to_bg_process("HOSTNAMES_ADD", (args[0], args[1]))
    else:
        logger.error("Vulnerability type %s currently has no scans implemented", kind)

    if injection_results:
        logger.debug("Injection results : %s", json.dumps(injection_results))
        blocked = is_blocking_enabled()
        stack = get_clean_stacktrace()
        comms.send_data_to_bg_process(
            "ATTACK", (injection_results, context, blocked, stack)
        )
        if blocked:
            raise error_type(*error_args)
