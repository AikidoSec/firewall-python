"""Exports wrap_lambda_handler function"""

from aikido_firewall.context import Context
from aikido_firewall.helpers.logging import logger
from .events import is_gateway_event, is_sqs_event
from .get_context_from_sqs_event import get_context_from_sqs_event
from .get_context_from_gateway_event import get_context_from_gateway_event
from aikido_firewall.background_process.cloud_connection_manager.globals import (
    get_global_cloud_connection_manager,
)


def wrap_lambda_handler(handler):
    """This wraps the lambda handler with aikido code"""

    def aikido_lambda_handler(event, context):
        context_json = {}
        try:
            if is_sqs_event(event):
                context_json = get_context_from_sqs_event(event)
            elif is_gateway_event(event):
                context_json = get_context_from_gateway_event(event)

            if not context_json:
                #  We don't know what the type of the event is
                #  We can't provide any context for the underlying sinks
                #  So we just run the handler without any context
                return handler(event, context)
            context = Context(context_obj=context_json)
            context.set_as_current_context()
        except Exception as e:
            logger.debug("Exception occured in AWS Lambda : %s", e)
        try:
            res = handler(event, context)
        finally:
            connection_manager = get_global_cloud_connection_manager()
            if connection_manager:
                # Send a last heartbeat before stopping :
                connection_manager.send_heartbeat()
        return res

    return aikido_lambda_handler
