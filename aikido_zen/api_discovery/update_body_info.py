"""Exports update_body_info function"""

from .get_body_info import get_body_info
from .merge_data_schemas import merge_data_schemas


def update_body_info(context, existing_body_info=None):
    """
    Merges two body info objects into one, getting all properties from both schemas to capture optional properties.
    If the body info is not defined, the existing body info is returned (if any).
    If there is no existing body info, but the new body info is defined, the new body info is returned without merging.
    """
    new_body_info = get_body_info(context)

    if new_body_info is None:
        return existing_body_info

    if existing_body_info is None:
        return new_body_info

    return {
        "type": new_body_info["type"],
        "schema": merge_data_schemas(
            existing_body_info["schema"], new_body_info["schema"]
        ),
    }
