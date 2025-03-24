"""Exports get_api_info function"""

from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.env_vars.feature_flags import is_feature_enabled
from .get_body_data_type import get_body_data_type
from .get_data_schema import get_data_schema
from .get_auth_types import get_auth_types


def get_api_info(context):
    """Generates an apispec based on the context passed along"""
    try:
        body_info = get_body_info(context)
        query_info = get_query_info(context)
        auth_info = get_auth_types(context)
        if body_info or query_info or auth_info:
            return {"body": body_info, "query": query_info, "auth": auth_info}
    except Exception as e:
        logger.debug("Exception occurred whilst generating apispec: %s", e)

    return {}


def get_body_info(context):
    """Returns type, schema dict with body info for the given context"""
    data = context.body
    if not data or not isinstance(data, dict):
        data = context.xml
    if not data or not isinstance(data, dict):
        return None
    return {
        "type": get_body_data_type(context.headers),
        "schema": get_data_schema(data),
    }


def get_query_info(context):
    """If context has query data this returns it's schema"""
    query_info = None
    if context.query and isinstance(context.query, dict) and len(context.query) > 0:
        query_info = get_data_schema(context.query)
    return query_info
