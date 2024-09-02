"""
Sink module for `pymongo`
"""

from copy import deepcopy
import importhook
from aikido_firewall.helpers.logging import logger
import aikido_firewall.background_process.packages as pkgs
import aikido_firewall.vulnerabilities as vulns

OPERATIONS_WITH_FILTER = [
    "replace_one",
    "update_one",
    "update_many",
    "delete_one",
    "delete_many",
    "find_one",
    "count_documents",
    "find_one_and_delete",
    "find_one_and_replace",
    "find_one_and_update",
]


# Synchronous :
@importhook.on_import("pymongo.collection")
def on_pymongo_import(pymongo):
    """
    Hook 'n wrap on `pymongo.collection`
    Our goal is to wrap the following functions in the Collection class :
    https://github.com/mongodb/mongo-python-driver/blob/98658cfd1fea42680a178373333bf27f41153759/pymongo/synchronous/collection.py#L136
    Returns : Modified pymongo.collection.Collection object
    """
    modified_pymongo = importhook.copy_module(pymongo)
    for operation in OPERATIONS_WITH_FILTER:
        if not hasattr(pymongo.Collection, operation):
            logger.warning("Operation `%s` not found on Collection object.", operation)

        prev_func = deepcopy(getattr(pymongo.Collection, operation))

        def wrapped_operation_function(
            self,
            filter,
            filter2=None,
            *args,
            prev_func=prev_func,
            op=operation,
            **kwargs,
        ):
            vulns.run_vulnerability_scan(
                kind="nosql_injection",
                op=f"pymongo.collection.Collection.{op}",
                args=(filter,),
            )
            if isinstance(filter2, dict):
                vulns.run_vulnerability_scan(
                    kind="nosql_injection",
                    op=f"pymongo.collection.Collection.{op}",
                    args=(filter2,),
                )
            if filter2:
                return prev_func(self, filter, filter2, *args, **kwargs)
            return prev_func(self, filter, *args, **kwargs)

        setattr(modified_pymongo.Collection, operation, wrapped_operation_function)

    pkgs.add_wrapped_package("pymongo")
    return modified_pymongo
