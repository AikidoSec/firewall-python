"""Exports request_handler function"""

import aikido_zen.background_process as communications
import aikido_zen.context as ctx
from aikido_zen.api_discovery.get_api_info import get_api_info
from aikido_zen.api_discovery.update_route_info import update_route_info
from aikido_zen.helpers.is_useful_route import is_useful_route
from aikido_zen.helpers.logging import logger
from aikido_zen.thread.thread_cache import get_cache


def on_post_request(status_code=0):
    """Checks if the current route is useful"""
    try:
        _on_post_request(status_code)
    except Exception as e:
        logger.debug("Exception occurred whilst running post request handler: %s", e)


def _on_post_request(status_code=0):
    context = ctx.get_current_context()
    comms = communications.get_comms()
    if not context or not comms:
        return
    is_curr_route_useful = is_useful_route(
        status_code,
        context.route,
        context.method,
    )
    if not is_curr_route_useful:
        return
    route_metadata = context.get_route_metadata()
    cache = get_cache()
    if cache:
        route = cache.routes.get(route_metadata)
        if not route:
            # This route does not exist yet, initialize it:
            cache.routes.initialize_route(route_metadata)
            comms.send_data_to_bg_process("INITIALIZE_ROUTE", route_metadata)
        # Run API Discovery :
        update_route_info(
            new_apispec=get_api_info(context), route=cache.routes.get(route_metadata)
        )
        # Add hit :
        cache.routes.increment_route(route_metadata)
