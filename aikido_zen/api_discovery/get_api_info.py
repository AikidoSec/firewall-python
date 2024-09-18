"""Exports get_api_info function"""

from aikido_zen.helpers.logging import logger
from aikido_zen.helpers.env_vars.feature_flags import is_feature_enabled
from .get_body_data_type import get_body_data_type
from .get_data_schema import get_data_schema


def get_api_info(context):
    """Gives you an object with type and schema"""
    # Check if feature flag COLLECT_API_SCHEMA is enabled
    if not is_feature_enabled("COLLECT_API_SCHEMA"):
        return None
    data = context.body
    if not data or not isinstance(data, dict):
        data = context.xml
    if not data or not isinstance(data, dict):
        return None

    try:
        return {
            "type": get_body_data_type(context.headers),
            "schema": get_data_schema(data),
        }
    except Exception as e:
        logger.debug("Exception occured whilst getting body data : %s", e)
        return None
