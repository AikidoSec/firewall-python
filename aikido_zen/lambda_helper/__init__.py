from aikido_zen.background_process import get_comms
from aikido_zen.thread.thread_cache import renew as process_cache_renew
from aikido_zen.helpers.logging import logger

LAMBDA_SEND_HEARTBEAT_TIMEOUT = 500 / 1000  # 500ms


def protect_lambda(handler):
    """Aikido protect function for the lambda"""

    def wrapper(*args, **kwargs):

        # Before

        rv = handler(*args, **kwargs)

        # After
        lambda_post_handler()

        return rv

    return wrapper


def lambda_post_handler():
    """
    Lambda post handler, after the lambda is finished, we want to flush the data to core
    """
    ipc_client = get_comms()
    if not ipc_client:
        logger.warning("Lambda: Failed to flush data, no IPC Client available.")
        return

    # Flush data from this process
    process_cache_renew()

    # Flush data from background process
    res = ipc_client.send_data_to_bg_process(
        action="SEND_HEARTBEAT",
        obj=None,
        receive=True,
        timeout_in_sec=LAMBDA_SEND_HEARTBEAT_TIMEOUT,
    )
    if res["success"]:
        logger.info("Lambda: successfully flushed data.")
    else:
        logger.warning("Lambda: Failed to flush data, error %s.", res["error"])
