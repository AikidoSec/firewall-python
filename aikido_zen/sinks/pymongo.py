"""
Sink module for `pymongo`
"""

from copy import deepcopy
import aikido_zen.importhook as importhook
from aikido_zen.helpers.logging import logger
import aikido_zen.background_process.packages as pkgs
import aikido_zen.vulnerabilities as vulns

# find_one not present in list since find_one calls find function.

OPERATIONS_WITH_FILTER = [
    ("replace_one", [0, "filter"]),
    ("update_one", [0, "filter"]),
    ("update_many", [0, "filter"]),
    ("delete_one", [0, "filter"]),
    ("delete_many", [0, "filter"]),
    ("count_documents", [0, "filter"]),
    ("find_one_and_delete", [0, "filter"]),
    ("find_one_and_replace", [0, "filter"]),
    ("find_one_and_update", [0, "filter"]),
    ("find", [0, "filter"]),
    ("find_raw_batches", [0, "filter"]),
    ("distinct", [1, "filter"]),
    ("watch", [0, "pipeline"]),
    ("aggregate", [0, "pipeline"]),
    ("aggregate_raw_batches", [0, "pipeline"]),
]

REQUIRED_PYMONGO_VERSION = "3.10.0"


# Synchronous :
@importhook.on_import("pymongo.collection")
def on_pymongo_import(pymongo):
    """
    Hook 'n wrap on `pymongo.collection`
    Our goal is to wrap the following functions in the Collection class :
    https://github.com/mongodb/mongo-python-driver/blob/98658cfd1fea42680a178373333bf27f41153759/pymongo/synchronous/collection.py#L136
    Returns : Modified pymongo.collection.Collection object
    """
    if not pkgs.pkg_compat_check("pymongo", REQUIRED_PYMONGO_VERSION):
        return pymongo
    modified_pymongo = importhook.copy_module(pymongo)
    for op_data in OPERATIONS_WITH_FILTER:
        op = op_data[0]
        if not hasattr(pymongo.Collection, op):
            logger.warning("Operation `%s` not found on Collection object.", op)

        prev_func = deepcopy(getattr(pymongo.Collection, op))

        def wrapped_op_func(
            self,
            *args,
            prev_func=prev_func,
            op_data=op_data,
            **kwargs,
        ):
            op, spot, key = op_data[0], op_data[1][0], op_data[1][1]
            data = None
            if kwargs.get(key, None):
                # Keyword found, setting data
                data = kwargs.get(key)
            elif len(args) > spot and args[spot]:
                data = args[spot]
            if data:
                vulns.run_vulnerability_scan(
                    kind="nosql_injection",
                    op=f"pymongo.collection.Collection.{op}",
                    args=(data,),
                )

            return prev_func(self, *args, **kwargs)

        setattr(modified_pymongo.Collection, op, wrapped_op_func)

    # Add bulk_write support :
    former_bulk_write = deepcopy(pymongo.Collection.bulk_write)

    def aikido_bulk_write(self, requests, *args, **kwargs):
        for request in requests:
            if hasattr(request, "_filter"):
                # Requested operation has a filter
                vulns.run_vulnerability_scan(
                    kind="nosql_injection",
                    op="pymongo.collection.Collection.bulk_write",
                    args=(request._filter,),
                )
        return former_bulk_write(self, requests, *args, **kwargs)

    setattr(modified_pymongo.Collection, "bulk_write", aikido_bulk_write)
    return modified_pymongo
