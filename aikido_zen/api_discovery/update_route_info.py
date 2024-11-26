"""Exports update_route_info function"""

from aikido_zen.helpers.logging import logger
from .merge_data_schemas import merge_data_schemas
from .merge_auth_types import merge_auth_types

ANALYSIS_ON_FIRST_X_ROUTES = 20


def update_route_info(new_apispec, route):
    """
    Checks if a route still needs to be updated (only analyzes first x routes),
    and if so, updates route using update_api_info
    """
    if route["hits"] <= ANALYSIS_ON_FIRST_X_ROUTES:
        # Only analyze the first x routes for api discovery
        route["apispec"] = update_api_info(new_apispec, route["apispec"])


def update_api_info(new_apispec, existing_apispec=None):
    """
    Merges two apispec objects into one, getting all properties from both schemas to capture optional properties.
    If the body info is not defined, the existing body info is returned (if any).
    If there is no existing body info, but the new body info is defined, the new body info is returned without merging.
    """
    try:
        if not new_apispec:
            return existing_apispec
        if not existing_apispec:
            return new_apispec

        # Body :
        existing_body = existing_apispec.get("body")
        if existing_body and new_apispec.get("body"):
            new_schema = new_apispec["body"].get("schema")
            existing_apispec["body"] = {
                "type": new_apispec["body"]["type"],
                "schema": merge_data_schemas(existing_body["schema"], new_schema),
            }
        elif new_apispec.get("body"):
            existing_apispec["body"] = new_apispec["body"]

        # Query :
        existing_query = existing_apispec.get("query")
        if existing_query and new_apispec.get("query"):
            existing_apispec["query"] = merge_data_schemas(
                existing_query, new_apispec["query"]
            )
        elif new_apispec.get("query"):
            existing_apispec["query"] = new_apispec["query"]

        # Auth :
        existing_apispec["auth"] = merge_auth_types(
            existing_apispec.get("auth"), new_apispec.get("auth")
        )
        return existing_apispec
    except Exception as e:
        logger.debug("Exception occured in update_api_info : %s", e)
