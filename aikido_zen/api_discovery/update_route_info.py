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
        route["apispec"] = update_api_info(context, route["apispec"])


def update_api_info(context, existing_apispec=None):
    """
    Merges two apispec objects into one, getting all properties from both schemas to capture optional properties.
    If the body info is not defined, the existing body info is returned (if any).
    If there is no existing body info, but the new body info is defined, the new body info is returned without merging.
    """
    new_apispec = get_api_info(context)

    if new_apispec == {}:
        return existing_apispec

    if existing_apispec == {}:
        return new_apispec

    if existing_apispec.get("body", None) and new_apispec.get("body", None):
        existing_schema = existing_apispec["body"].get("schema", None)
        new_schema = new_apispec["body"].get("schema", None)
        existing_apispec["body"] = {
            "type": new_apispec["body"]["type"],
            "schema": merge_data_schemas(existing_schema, new_schema),
        }
    elif new_apispec.get("body", None):
        existing_apispec["body"] = new_apispec["body"]
    return existing_apispec
