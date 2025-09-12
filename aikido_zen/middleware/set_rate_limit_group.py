from typing import Union

from aikido_zen.context import get_current_context
from aikido_zen.helpers.logging import logger


def set_rate_limit_group(group_id: Union[str, int]):
    if not group_id:
        logger.warning("Group ID cannot be empty.")
        return

    # Check if it's string of number, ensure string.
    if not isinstance(group_id, str) and not isinstance(group_id, int):
        logger.warning("Group ID must be a string or a number")
        return
    group_id = str(group_id)

    context = get_current_context()
    if not context:
        logger.warning(
            "set_rate_limit_group(...) was called without a context. Make sure to call set_rate_limit_group(...) within an HTTP request."
        )
        return

    if context.executed_middleware:
        logger.warning(
            "set_rate_limit_group(...) must be called before the Zen middleware is executed."
        )

    context.rate_limit_group = group_id
    context.set_as_current_context()
