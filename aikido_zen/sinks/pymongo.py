"""
Sink module for `pymongo`
"""

from wrapt import when_imported

from aikido_zen.helpers.get_argument import get_argument
import aikido_zen.background_process.packages as pkgs
import aikido_zen.vulnerabilities as vulns
from . import try_wrap_function_wrapper
from ..errors import AikidoException

REQUIRED_PYMONGO_VERSION = "3.10.0"


@when_imported("pymongo.collection")
def patch(m):
    """
    patching pymongo.collection
    - patches Collection.*(filter, ...)
    - patches Collection.*(..., filter, ...)
    - patches Collection.*(pipeline, ...)
    - patches Collection.bulk_write
    src: https://github.com/mongodb/mongo-python-driver/blob/98658cfd1fea42680a178373333bf27f41153759/pymongo/synchronous/collection.py#L136
    """
    if not pkgs.is_package_compatible("pymongo", REQUIRED_PYMONGO_VERSION):
        return

    # func(filter, ...)
    try_wrap_function_wrapper(m, "Collection.replace_one", _func_filter_first)
    try_wrap_function_wrapper(m, "Collection.update_one", _func_filter_first)
    try_wrap_function_wrapper(m, "Collection.update_many", _func_filter_first)
    try_wrap_function_wrapper(m, "Collection.delete_one", _func_filter_first)
    try_wrap_function_wrapper(m, "Collection.delete_many", _func_filter_first)
    try_wrap_function_wrapper(m, "Collection.count_documents", _func_filter_first)
    try_wrap_function_wrapper(m, "Collection.find_one_and_delete", _func_filter_first)
    try_wrap_function_wrapper(m, "Collection.find_one_and_replace", _func_filter_first)
    try_wrap_function_wrapper(m, "Collection.find_one_and_update", _func_filter_first)
    try_wrap_function_wrapper(m, "Collection.find", _func_filter_first)
    try_wrap_function_wrapper(m, "Collection.find_raw_batches", _func_filter_first)
    # find_one not present in list since find_one calls find function.

    # func(..., filter, ...)
    try_wrap_function_wrapper(m, "Collection.distinct", _func_filter_second)

    # func(pipeline, ...)
    try_wrap_function_wrapper(m, "Collection.watch", _func_pipeline)
    try_wrap_function_wrapper(m, "Collection.aggregate", _func_pipeline)
    try_wrap_function_wrapper(m, "Collection.aggregate_raw_batches", _func_pipeline)

    # bulk_write
    try_wrap_function_wrapper(m, "Collection.bulk_write", _bulk_write)


def _func_filter_first(func, instance, args, kwargs):
    """Collection.func(filter, ...)"""
    nosql_filter = get_argument(args, kwargs, 0, "filter")
    if not nosql_filter:
        return func(*args, **kwargs)

    vulns.run_vulnerability_scan(
        kind="nosql_injection",
        op=f"pymongo.collection.Collection.{func.__name__}",
        args=(nosql_filter,),
    )
    return func(*args, **kwargs)


def _func_filter_second(func, instance, args, kwargs):
    """Collection.func(..., filter, ...)"""
    nosql_filter = get_argument(args, kwargs, 1, "filter")
    if not nosql_filter:
        return func(*args, **kwargs)

    vulns.run_vulnerability_scan(
        kind="nosql_injection",
        op=f"pymongo.collection.Collection.{func.__name__}",
        args=(nosql_filter,),
    )
    return func(*args, **kwargs)


def _func_pipeline(func, instance, args, kwargs):
    """Collection.func(pipeline, ...)"""
    nosql_pipeline = get_argument(args, kwargs, 0, "pipeline")
    if not nosql_pipeline:
        return func(*args, **kwargs)

    vulns.run_vulnerability_scan(
        kind="nosql_injection",
        op=f"pymongo.collection.Collection.{func.__name__}",
        args=(nosql_pipeline,),
    )
    return func(*args, **kwargs)


def _bulk_write(func, instance, args, kwargs):
    requests = get_argument(args, kwargs, 0, "requests")

    # Filter requests that contain "_filter"
    requests_with_filter = [req for req in requests if hasattr(req, "_filter")]
    # Run vulnerability scans for each filtered request
    for request in requests_with_filter:
        try:
            vulns.run_vulnerability_scan(
                kind="nosql_injection",
                op="pymongo.collection.Collection.bulk_write",
                args=(request._filter,),
            )
        except AikidoException as e:
            raise e
        except Exception:
            pass  # Log or handle the exception if needed

    return func(*args, **kwargs)
