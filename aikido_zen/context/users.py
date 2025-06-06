"""
Users file
"""

from aikido_zen.helpers.logging import logger
from . import get_current_context
import aikido_zen.thread.thread_cache as thread_cache
import aikido_zen.helpers.get_current_unixtime_ms as t


def set_user(user):
    """
    External function for applications to set a user
    """
    validated_user = validate_user(user)
    if not validated_user:
        return
    logger.debug("Validated user : %s", validated_user)

    context = get_current_context()
    if not context:
        logger.debug("No context set, returning")
        return
    if context.executed_middleware is True:
        # Middleware to rate-limit/check for users ran already. Could be misconfiguration.
        logger.warning(
            "set_user(...) must be called before the Zen middleware is executed."
        )

    validated_user["lastIpAddress"] = context.remote_address
    context.user = validated_user

    # Send validated_user object to background process :
    cache = thread_cache.get_cache()
    if cache:
        cache.users.add_user(
            user_id=validated_user["id"],
            user_name=validated_user["name"],
            user_ip=validated_user["lastIpAddress"],
            current_time=t.get_unixtime_ms(),
        )


def validate_user(user):
    """This validates the user object"""
    if not isinstance(user, dict):
        logger.info(
            "set_user(...) expects a dict with 'id' and 'name' properties, found %s instead.",
            type(user),
        )
        return

    #  Validate user's id :
    if not "id" in user:
        logger.info("set_user(...) expects an object with 'id' property.")
        return
    if not isinstance(user["id"], str) and not isinstance(user["id"], int):
        logger.info(
            "set_user(...) expects an object with 'id' property of type string or number, found %s instead.",
            type(user["id"]),
        )
        return
    if isinstance(user["id"], str) and len(user["id"]) == 0:
        logger.info(
            "set_user(...) expects an object with 'id' property non-empty string."
        )
        return
    valid_user = {"id": str(user["id"])}
    if "name" in user and isinstance(user["name"], str) and len(user["name"]) > 0:
        valid_user["name"] = str(user["name"])

    return valid_user
