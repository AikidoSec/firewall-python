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
)
from aikido_firewall.background_process import get_comms
from aikido_firewall.helpers.logging import logger
from aikido_firewall.helpers.blocking_enabled import is_blocking_enabled
from .sql_injection.context_contains_sql_injection import context_contains_sql_injection
from .nosql_injection.check_context import check_context_for_nosql_injection
from .shell_injection.check_context_for_shell_injection import (
    check_context_for_shell_injection,
)
from .path_traversal.check_context_for_path_traversal import (
    check_context_for_path_traversal,
)


def run_vulnerability_scan(kind, op, args):
    """
    Generally checks context for the provided "kind" of injection,
    raises error if blocking is enabled, communicates it with reporter
    """
    context = get_current_context()
    if not context:
        return

    error_type = AikidoException  # Default error
    injection_results = {}

    if kind == "sql_injection":
        injection_results = context_contains_sql_injection(
            sql=args[0], dialect=args[1], operation=op, context=context
        )
        error_type = AikidoSQLInjection
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
    else:
        logger.error("Vulnerability type %s currently has no scans implemented", kind)

    if injection_results:
        logger.debug("Injection results : %s", json.dumps(injection_results))
        get_comms().send_data_to_bg_process("ATTACK", (injection_results, context))
        if is_blocking_enabled():
            raise error_type()
