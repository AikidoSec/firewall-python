"""
Sink module for `psycopg`
"""

import copy
import aikido_zen.importhook as importhook
from aikido_zen.vulnerabilities.sql_injection.dialects import Postgres
from aikido_zen.background_process.packages import pkg_compat_check
import aikido_zen.vulnerabilities as vulns

REQUIRED_PSYCOPG_VERSION = "3.1.0"


@importhook.on_import("psycopg.cursor")
def on_psycopg_import(psycopg):
    """
    Hook 'n wrap on `psycopg.connect` function, we modify the cursor_factory
    of the result of this connect function.
    """
    if not pkg_compat_check("psycopg", REQUIRED_PSYCOPG_VERSION):
        return psycopg
    modified_psycopg = importhook.copy_module(psycopg)
    former_copy_funtcion = copy.deepcopy(psycopg.Cursor.copy)
    former_execute_function = copy.deepcopy(psycopg.Cursor.execute)
    former_executemany_function = copy.deepcopy(psycopg.Cursor.executemany)

    def aikido_copy(self, statement, params=None, *args, **kwargs):
        sql = statement
        vulns.run_vulnerability_scan(
            kind="sql_injection", op="psycopg.Cursor.copy", args=(sql, Postgres())
        )
        return former_copy_funtcion(self, statement, params, *args, **kwargs)

    def aikido_execute(self, query, params=None, *args, **kwargs):
        sql = query
        vulns.run_vulnerability_scan(
            kind="sql_injection", op="psycopg.Cursor.execute", args=(sql, Postgres())
        )
        return former_execute_function(self, query, params, *args, **kwargs)

    def aikido_executemany(self, query, params_seq):
        args = (query, Postgres())
        op = "psycopg.Cursor.executemany"
        vulns.run_vulnerability_scan(kind="sql_injection", op=op, args=args)
        return former_executemany_function(self, query, params_seq)

    setattr(psycopg.Cursor, "copy", aikido_copy)  # pylint: disable=no-member
    setattr(psycopg.Cursor, "execute", aikido_execute)  # pylint: disable=no-member
    # pylint: disable=no-member
    setattr(psycopg.Cursor, "executemany", aikido_executemany)

    return modified_psycopg
