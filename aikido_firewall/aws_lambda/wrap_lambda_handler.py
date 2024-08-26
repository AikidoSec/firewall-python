"""Exports wrap_lambda_handler function"""

from aikido_firewall.context import Context
from .events import is_gateway_event, is_sqs_event
from .get_context_from_sqs_event import get_context_from_sqs_event
from .get_context_from_gateway_event import get_context_from_gateway_event


def wrap_lambda_handler(handler):
    """This wraps the lambda handler with aikido code"""

    def aikido_lambda_handler(event, context):
        context_json = {}
        if is_sqs_event(event):
            context_json = get_context_from_sqs_event(event)
        elif is_gateway_event(event):
            context_json = get_context_from_gateway_event(event)
        if not context_json:
            return handler(event, context)
        context = Context(context_obj=context_json)
        context.set_as_current_context()

    return aikido_lambda_handler
