"""
Init.py file for starlette module
---
Starlette wrapping is subdivided in two parts :
- starlette.applications : Wraps __call__ on Starlette class to run "init" stage.
- starlette.routing : request_response function : Run pre_response code and 
    also runs post_response code after getting response from user function.

Folder also includes helper functions : 
- extract_data_from_request, which will extract the data from a request object safely,
    e.g. body, json, form. This also saves it inside the current context.
"""

import aikido_zen.importhook as importhook
from aikido_zen.background_process.packages import is_package_compatible, ANY_VERSION


@importhook.on_import("starlette")
def on_starlette_import(starlette):
    """
    This checks for the package version of starlette so you don't have to do it twice,
    once in starlette_applications and once in starlette_applications.
    """
    if not is_package_compatible("starlette", required_version=ANY_VERSION):
        return starlette
    # Package is compatible, start wrapping :
    import aikido_zen.sources.starlette.starlette_applications
    import aikido_zen.sources.starlette.starlette_routing
