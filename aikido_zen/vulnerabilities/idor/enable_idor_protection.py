from aikido_zen.helpers.logging import logger
from aikido_zen.storage.idor_protection_config import (
    IdorProtectionConfig,
    idor_protection_store,
)


def enable_idor_protection(tenant_column_name: str, excluded_tables=None):
    if not isinstance(tenant_column_name, str):
        logger.info(
            "enable_idor_protection(...) expects tenant_column_name to be a string, found %s instead.",
            type(tenant_column_name),
        )
        return

    if len(tenant_column_name) == 0:
        logger.info(
            "enable_idor_protection(...) expects tenant_column_name to be a non-empty string."
        )
        return

    if excluded_tables is None:
        excluded_tables = []

    if not isinstance(excluded_tables, list):
        logger.info(
            "enable_idor_protection(...) expects excluded_tables to be a list, found %s instead.",
            type(excluded_tables),
        )
        return

    for table in excluded_tables:
        if not isinstance(table, str):
            logger.info(
                "enable_idor_protection(...) expects excluded_tables to contain strings, found %s instead.",
                type(table),
            )
            return

    idor_protection_store.set(IdorProtectionConfig(tenant_column_name, excluded_tables))
