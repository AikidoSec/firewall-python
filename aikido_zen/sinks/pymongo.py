"""
Sink module for `pymongo`
"""

import wrapt

from aikido_zen.helpers.get_argument import get_argument
import aikido_zen.vulnerabilities as vulns
from . import patch_function, on_import, before
from aikido_zen.helpers.register_call import register_call
from aikido_zen.helpers.logging import logger


@before
def _func_filter_first(func, instance, args, kwargs):
    """Collection.func(filter, ...)"""
    nosql_filter = get_argument(args, kwargs, 0, "filter")
    if not nosql_filter:
        return

    operation = f"pymongo.collection.Collection.{func.__name__}"
    register_call(operation, "nosql_op")

    vulns.run_vulnerability_scan(
        kind="nosql_injection",
        op=operation,
        args=(nosql_filter,),
    )


@before
def _func_filter_second(func, instance, args, kwargs):
    """Collection.func(..., filter, ...)"""
    nosql_filter = get_argument(args, kwargs, 1, "filter")
    if not nosql_filter:
        return

    operation = f"pymongo.collection.Collection.{func.__name__}"
    register_call(operation, "nosql_op")

    vulns.run_vulnerability_scan(
        kind="nosql_injection",
        op=operation,
        args=(nosql_filter,),
    )


@before
def _func_pipeline(func, instance, args, kwargs):
    """Collection.func(pipeline, ...)"""
    nosql_pipeline = get_argument(args, kwargs, 0, "pipeline")
    if not nosql_pipeline:
        return

    operation = f"pymongo.collection.Collection.{func.__name__}"
    register_call(operation, "nosql_op")

    vulns.run_vulnerability_scan(
        kind="nosql_injection",
        op=operation,
        args=(nosql_pipeline,),
    )


@before
def _bulk_write(func, instance, args, kwargs):
    requests = get_argument(args, kwargs, 0, "requests")

    operation = "pymongo.collection.Collection.bulk_write"
    register_call(operation, "nosql_op")

    # Filter requests that contain "_filter"
    requests_with_filter = [req for req in requests if hasattr(req, "_filter")]
    for request in requests_with_filter:
        vulns.run_vulnerability_scan(
            kind="nosql_injection",
            op=operation,
            args=(request._filter,),
        )


def patch_collection(m):
    """
    patching pymongo.collection
    - patches Collection.*(filter, ...)
    - patches Collection.*(..., filter, ...)
    - patches Collection.*(pipeline, ...)
    - patches Collection.bulk_write
    src: https://github.com/mongodb/mongo-python-driver/blob/98658cfd1fea42680a178373333bf27f41153759/pymongo/synchronous/collection.py#L136
    """

    if m.__name__ == "pymongo.collection":
        # pymongo together with motor causes issues here, with the wrapping happening twice,
        # since pymongo.collection still exists, but it just imports everything from pymono.synchronous.collection
        original_collection_class = wrapt.resolve_path(m, "Collection")[2]
        if original_collection_class.__module__ != "pymongo.collection":
            return

    # func(filter, ...)
    patch_function(m, "Collection.replace_one", _func_filter_first)
    patch_function(m, "Collection.update_one", _func_filter_first)
    patch_function(m, "Collection.update_many", _func_filter_first)
    patch_function(m, "Collection.delete_one", _func_filter_first)
    patch_function(m, "Collection.delete_many", _func_filter_first)
    patch_function(m, "Collection.count_documents", _func_filter_first)
    patch_function(m, "Collection.find_one_and_delete", _func_filter_first)
    patch_function(m, "Collection.find_one_and_replace", _func_filter_first)
    patch_function(m, "Collection.find_one_and_update", _func_filter_first)
    patch_function(m, "Collection.find", _func_filter_first)
    patch_function(m, "Collection.find_raw_batches", _func_filter_first)
    # find_one not present in list since find_one calls find function.

    # func(..., filter, ...)
    patch_function(m, "Collection.distinct", _func_filter_second)

    # func(pipeline, ...)
    patch_function(m, "Collection.watch", _func_pipeline)
    patch_function(m, "Collection.aggregate", _func_pipeline)
    patch_function(m, "Collection.aggregate_raw_batches", _func_pipeline)

    # bulk_write
    patch_function(m, "Collection.bulk_write", _bulk_write)


@on_import("pymongo", "pymongo", version_requirement="3.10.0")
def patch(m):
    on_import("pymongo.collection")(patch_collection)
    # After 4.9, pymongo moved the collection module to `synchronous`
    on_import("pymongo.synchronous.collection")(patch_collection)
