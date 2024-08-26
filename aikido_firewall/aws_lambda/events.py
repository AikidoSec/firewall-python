"""Exports helper functions to determine Lambda events"""

from aikido_firewall.helpers.is_plain_object import is_plain_object


def is_sqs_event(event):
    """Checks if the event provided is an SQS event"""
    return is_plain_object(event) and "Records" in event


def is_gateway_event(event):
    """Check if the event is an API Gateway event."""
    return is_plain_object(event) and "httpMethod" in event and "headers" in event
