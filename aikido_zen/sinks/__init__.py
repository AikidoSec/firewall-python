import threading

from wrapt import wrap_object, FunctionWrapper, when_imported, resolve_path
from aikido_zen.background_process.packages import ANY_VERSION, is_package_compatible
from aikido_zen.errors import AikidoException
from aikido_zen.helpers.logging import logger


def on_import(name, package="", version_requirement=ANY_VERSION):
    """
    Decorator to register a function to be called when a package is imported.
    It checks if the package is compatible with the specified version requirement.
    """

    def decorator(func):
        def check_pkg_wrapper(f):
            def wrapper(*args, **kwargs):
                # This code runs only on import
                if package and not is_package_compatible(package, version_requirement):
                    return
                return f(*args, **kwargs)

            return wrapper

        # Register the function to be called on import
        when_imported(name)(check_pkg_wrapper(func))

    return decorator


def patch_function(module, name, wrapper):
    """
    Patches a function in the specified module with a wrapper function.
    """
    try:
        (_, _, original) = resolve_path(module, name)

        hook_duplicate_helper = HookDuplicateHelper(original, wrapper)

        if not hook_duplicate_helper.is_registered():
            wrap_object(module, name, FunctionWrapper, (wrapper,))
            hook_duplicate_helper.register()
        else:
            logger.debug(
                "Attempted to apply same hook twice: %s", hook_duplicate_helper.hook_id
            )
    except Exception as e:
        logger.info("Failed to wrap %s:%s, due to: %s", module, name, e)


class HookDuplicateHelper:
    AIKIDO_HOOKS_LOCK = "_aikido_hooks_lock"
    AIKIDO_HOOKS_STORE = "_aikido_hooks_store"

    def __init__(self, original, wrapper):
        self.original = original

        # Hook id is either module+name, or set via @before, ... as _hook_id
        self.hook_id = f"{wrapper.__module__}:wrapper.__name__"
        if hasattr(wrapper, "_hook_id"):
            self.hook_id = getattr(wrapper, "_hook_id")

    def is_registered(self):
        self._try_create_hooks_store()
        if not hasattr(self.original, self.AIKIDO_HOOKS_LOCK):
            return False
        with getattr(self.original, self.AIKIDO_HOOKS_LOCK):
            return self.hook_id in getattr(self.original, self.AIKIDO_HOOKS_STORE)

    def register(self):
        self._try_create_hooks_store()
        if not hasattr(self.original, self.AIKIDO_HOOKS_LOCK):
            return False
        with getattr(self.original, self.AIKIDO_HOOKS_LOCK):
            getattr(self.original, self.AIKIDO_HOOKS_STORE).add(self.hook_id)

    def _try_create_hooks_store(self):
        if hasattr(self.original, self.AIKIDO_HOOKS_LOCK):
            return
        try:
            setattr(self.original, self.AIKIDO_HOOKS_LOCK, threading.Lock())
            setattr(self.original, self.AIKIDO_HOOKS_STORE, set())
        except AttributeError as e:
            logger.debug("Failed to create hook storage on: %s", self.original)


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

    decorator._hook_id = f"{wrapper.__module__}:{wrapper.__name__}"
    return decorator


def before_async(wrapper):
    """
    Surrounds an async patch with try-except and calls the original asynchronous function at the end
    """

    async def decorator(func, instance, args, kwargs):
        try:
            await wrapper(func, instance, args, kwargs)  # Call the patch
        except AikidoException as e:
            raise e  # Re-raise AikidoException
        except Exception as e:
            logger.debug(
                "%s:%s wrapping-before error: %s", func.__module__, func.__name__, e
            )
        return await func(*args, **kwargs)  # Call the original function

    decorator._hook_id = f"{wrapper.__module__}:{wrapper.__name__}"
    return decorator


def before_modify_return(wrapper):
    """
    Surrounds a patch with try-except and calls the original function at the end unless a return value is present.
    """

    def decorator(func, instance, args, kwargs):
        try:
            rv = wrapper(func, instance, args, kwargs)  # Call the patch
            if rv is not None:
                return rv
        except AikidoException as e:
            raise e  # Re-raise AikidoException
        except Exception as e:
            logger.debug(
                "%s:%s wrapping-before error: %s", func.__module__, func.__name__, e
            )
        return func(*args, **kwargs)  # Call the original function

    decorator._hook_id = f"{wrapper.__module__}:{wrapper.__name__}"
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

    decorator._hook_id = f"{wrapper.__module__}:{wrapper.__name__}"
    return decorator
