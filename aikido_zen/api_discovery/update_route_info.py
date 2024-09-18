"""Exports update_route_info function"""

from .get_api_info import get_api_info
from .merge_data_schemas import merge_data_schemas

ANALYSIS_ON_FIRST_X_ROUTES = 20


def update_route_info(context, route):
    """
    Checks if a route still needs to be updated (only analyzes first x routes),
    and if so, updates route using update_api_info
    """
    if route["hits"] <= ANALYSIS_ON_FIRST_X_ROUTES:
        # Only analyze the first x routes for api discovery
        route["body"] = update_api_info(context, route["body"])


def update_api_info(context, existing_api_info=None):
    """
    Merges two apispec objects into one, getting all properties from both schemas to capture optional properties.
    If the body info is not defined, the existing body info is returned (if any).
    If there is no existing body info, but the new body info is defined, the new body info is returned without merging.
    """
    new_api_info = get_api_info(context)

    if new_api_info is None:
        return existing_api_info

    if existing_api_info is None:
        return new_api_info

    return {
        "type": new_api_info["type"],
        "schema": merge_data_schemas(
            existing_api_info["schema"], new_api_info["schema"]
        ),
    }
