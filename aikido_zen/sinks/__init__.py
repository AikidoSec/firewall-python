from wrapt import wrap_object, FunctionWrapper

from aikido_zen.helpers.logging import logger


def try_wrap_function_wrapper(module, name, wrapper):
    try:
        wrap_object(module, name, FunctionWrapper, (wrapper,))
    except Exception as e:
        logger.info("Failed to wrap %s, due to: %s", module, e)
