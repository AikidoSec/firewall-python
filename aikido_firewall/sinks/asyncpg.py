"""
Sink module for `asyncpg`
"""

import copy
import aikido_firewall.importhook as importhook
from aikido_firewall.vulnerabilities.sql_injection.dialects import Postgres
from aikido_firewall.background_process.packages import add_wrapped_package
import aikido_firewall.vulnerabilities as vulns
from aikido_firewall.helpers.logging import logger


@importhook.on_import("asyncpg.connection")
def on_asyncpg_import(asyncpg):
    """
    Hook 'n wrap on `asyncpg.connection`
    * the Cursor classes in asyncpg.cursor are only used to fetch data. (Currently not supported)
    * Pool class uses Connection class (Wrapping supported for Connection class)
    * _execute(...) get's called by all except execute and executemany
    Our goal is to wrap the _execute(), execute(), executemany() functions in Connection class :
    https://github.com/MagicStack/asyncpg/blob/85d7eed40637e7cad73a44ed2439ffeb2a8dc1c2/asyncpg/connection.py#L43
    Returns : Modified asyncpg.connection object
    """
    modified_asyncpg = importhook.copy_module(asyncpg)

    # pylint: disable=protected-access # We need to wrap this function
    former__execute = copy.deepcopy(asyncpg.Connection._execute)
    former_executemany = copy.deepcopy(asyncpg.Connection.executemany)
    former_execute = copy.deepcopy(asyncpg.Connection.execute)

    def aikido_new__execute(_self, query, *args, **kwargs):
        vulns.run_vulnerability_scan(
            kind="sql_injection",
            op="asyncpg.connection.Connection._execute",
            args=(query, Postgres()),
        )

        return former__execute(_self, query, *args, **kwargs)

    def aikido_new_executemany(_self, query, *args, **kwargs):
        # This query is just a string, not a list, see docs.
        vulns.run_vulnerability_scan(
            kind="sql_injection",
            op="asyncpg.connection.Connection.executemany",
            args=(query, Postgres()),
        )
        return former_executemany(_self, query, *args, **kwargs)

    def aikido_new_execute(_self, query, *args, **kwargs):
        vulns.run_vulnerability_scan(
            kind="sql_injection",
            op="asyncpg.connection.Connection.execute",
            args=(query, Postgres()),
        )
        return former_execute(_self, query, *args, **kwargs)

    # pylint: disable=no-member
    setattr(asyncpg.Connection, "_execute", aikido_new__execute)
    setattr(asyncpg.Connection, "executemany", aikido_new_executemany)
    setattr(asyncpg.Connection, "execute", aikido_new_execute)

    add_wrapped_package("asyncpg")
    return modified_asyncpg
