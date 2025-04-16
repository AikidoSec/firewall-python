from wrapt import wrap_object, FunctionWrapper, when_imported
from aikido_zen.background_process.packages import ANY_VERSION, is_package_compatible
from aikido_zen.errors import AikidoException
from aikido_zen.helpers.logging import logger


def on_import(name, package="", version_requirement=ANY_VERSION):
    """
    Decorator to register a function to be called when a package is imported.
    It checks if the package is compatible with the specified version requirement.
    """

    def decorator(func):
        if package and not is_package_compatible(package, version_requirement):
            return

        when_imported(name)(func)  # Register the function to be called on import

    return decorator


def patch_function(module, name, wrapper):
    """
    Patches a function in the specified module with a wrapper function.
    """
    try:
        wrap_object(module, name, FunctionWrapper, (wrapper,))
    except Exception as e:
        logger.info("Failed to wrap %s:%s, due to: %s", module, name, e)


def before(wrapper):
    """
    Surrounds a patch with try-except and calls the original function at the end
    """

    def decorator(func, instance, args, kwargs):
        try:
            wrapper(func, instance, args, kwargs)  # Call the patch
        except AikidoException as e:
            raise e  # Re-raise AikidoException
        except Exception as e:
            logger.debug(
                "%s:%s wrapping-before error: %s", func.__module__, func.__name__, e
            )

        return func(*args, **kwargs)  # Call the original function

    return decorator


def after(wrapper):
    """
    Surrounds a patch with try-except, calls the original function and gives the return value to the patch
    """

    def decorator(func, instance, args, kwargs):
        return_value = func(*args, **kwargs)  # Call the original function
        try:
            wrapper(func, instance, args, kwargs, return_value)  # Call the patch
        except AikidoException as e:
            raise e  # Re-raise AikidoException
        except Exception as e:
            logger.debug(
                "%s:%s wrapping-after error: %s", func.__module__, func.__name__, e
            )

        return return_value

    return decorator
