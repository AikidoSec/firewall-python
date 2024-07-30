"""
Sink module for `pymongo`
"""

from importlib.metadata import version
from copy import deepcopy
import importhook
from aikido_firewall.helpers.logging import logger

OPERATIONS_WITH_FILTER = [
    "replace_one",  # L1087
    "update_one",  # L1189
    "update_many",  # L1302
    "delete_one",  # L1542
    "delete_many",  # L1607
    "find_one",  # L1672
    "count_documents",  # L2020
    "find_one_and_delete",  # L3207
    "find_one_and_replace",  # L3296
    "find_one_and_update",  # L3403
]

# ISSUE : Asynchronous
# ISSUE : `find` on L1707 and `find_raw_batches` on L1895
# ISSUE : `aggregate` on L2847 and `aggregate_raw_batches` on L2942
# ISSUE : `distinct` on L3054


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
        old_function = deepcopy(getattr(pymongo.Collection, operation))

        def wrapped_operation_function(_self, filter, *args, **kwargs):
            logger.debug(" `pymongo.collection.Collection.%s` wrapped", operation)
            logger.debug(filter)
            old_function(_self, filter, *args, **kwargs)

        setattr(modified_pymongo.Collection, operation, wrapped_operation_function)

    logger.debug("Wrapped `pymongo` with version %s", version("pymongo"))
    return modified_pymongo