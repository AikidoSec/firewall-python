from aikido_zen.sinks import on_import, patch_function, after
import contextvars
import importlib.metadata
from importlib.metadata import PackageNotFoundError
from aikido_zen.background_process.packages import PackagesStore

running_import_scan = contextvars.ContextVar("running_import_scan", default=False)


@after
def _import(func, instance, args, kwargs, return_value):
    if running_import_scan.get():
        return
    running_import_scan.set(True)

    if not hasattr(return_value, "__file__"):
        return  # Would be built-in into the interpreter (system package)

    if not hasattr(return_value, "__package__"):
        return
    name = getattr(return_value, "__package__")

    if not name:
        # Make sure the name exists
        return
    name = name.split(".")[0]  # Remove submodules

    if PackagesStore.get_package(name):
        return

    version = None
    try:
        version = importlib.metadata.version(name)
    except PackageNotFoundError:
        pass
    if version:
        PackagesStore.add_package(name, version)

    running_import_scan.set(False)


@on_import("builtins")
def patch(m):
    """
    patching module builtins
    - patches builtins.__import__
    """
    patch_function(m, "__import__", _import)
