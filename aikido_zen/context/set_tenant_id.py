"""
Exports set_tenant_id for setting the tenant ID on the current context.
"""

from aikido_zen.helpers.logging import logger
from . import get_current_context


def set_tenant_id(tenant_id):
    """
    Sets the tenant ID on the current request context.
    Used for IDOR protection to verify SQL queries filter on the correct tenant.
    """
    if not isinstance(tenant_id, (str, int)):
        logger.info(
            "set_tenant_id(...) expects a string or integer, found %s instead.",
            type(tenant_id),
        )
        return

    str_id = str(tenant_id)
    if len(str_id) == 0:
        logger.info("set_tenant_id(...) expects a non-empty value.")
        return

    context = get_current_context()
    if not context:
        logger.debug("No context set, cannot set tenant_id")
        return

    context.tenant_id = str_id
