"""
Starlette wrapping is subdivided in two parts :
- starlette.applications : Wraps __call__ on Starlette class to run "init" stage.
- starlette.routing : request_response function : Run pre_response code and 
    also runs post_response code after getting response from user function.

Folder also includes helper functions : 
- extract_data_from_request, which will extract the data from a request object safely,
    e.g. body, json, form. This also saves it inside the current context.
"""

import aikido_zen.sources.starlette.starlette_applications
import aikido_zen.sources.starlette.starlette_routing
