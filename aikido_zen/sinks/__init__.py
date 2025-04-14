from wrapt import wrap_object, FunctionWrapper, when_imported

from aikido_zen.background_process.packages import ANY_VERSION, is_package_compatible
from aikido_zen.errors import AikidoException
from aikido_zen.helpers.logging import logger


def on_import(name, package="", version_requirement=ANY_VERSION):
    def decorator(func):
        # Reports package and checks version reqs (if necessary)
        if package and not is_package_compatible(package, version_requirement):
            return

        when_imported(name)(func)

    return decorator


def patch_function(module, name, wrapper):
    try:
        wrap_object(module, name, FunctionWrapper, (wrapper,))
    except Exception as e:
        logger.info("Failed to wrap %s, due to: %s", module, e)


def before(wrapper):
    def decorator(func, instance, args, kwargs):
        # try-except makes sure if we make a mistake in before wrapping it gets catch-ed
        try:
            wrapper(func, instance, args, kwargs)
        except AikidoException as e:
            raise e
        except Exception as e:
            logger.debug(
                "%s:%s wrapping-before error: %s", func.__module__, func.__name__, e
            )

        return func(*args, **kwargs)

    return decorator
