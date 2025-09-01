from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger

def set_rate_limit_group(group_id: str):
    if not group_id or not isinstance(group_id, str):
        logger.warning("")
        return

    context = get_current_context()
    if not context:
        logger.warning("")
        return

    if context.executed_middleware:
        logger.warning("")

    context.rate_limit_group = group_id
    context.set_as_current_context()

