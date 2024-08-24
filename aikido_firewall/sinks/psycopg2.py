"""
Sink module for `psycopg2`
"""

import copy
import importhook
from aikido_firewall.vulnerabilities.sql_injection.dialects import Postgres
from aikido_firewall.background_process.packages import add_wrapped_package
from aikido_firewall.vulnerabilities import run_vulnerability_scan
from aikido_firewall.helpers.logging import logger


def generate_aikido_cursor(cursor_class):

    class AikidoCursor(cursor_class):
        """Aikido's mutable cursor class"""

        def __init__(self, *args, **kwargs):
            # Initialize the base cursor class :
            super().__init__(*args, **kwargs)

            # Return a function dynamically

        def execute(self, *args, **kwargs):
            """Aikido's wrapped execute function"""
            logger.critical(args[0])

            run_vulnerability_scan(
                kind="sql_injection",
                op="psycopg2.Connection.Cursor.execute",
                args=(args[0], Postgres()),  #  args[0] : sql
            )
            return super().execute(*args, **kwargs)

        def executemany(self, *args, **kwargs):
            """Aikido's wrapped executemany function"""
            for sql in args[0]:
                run_vulnerability_scan(
                    kind="sql_injection",
                    op="psycopg2.Connection.Cursor.executemany",
                    args=(sql, Postgres()),
                )
            return super().executemany(*args, **kwargs)

    return AikidoCursor


@importhook.on_import("psycopg2")
def on_psycopg2_import(psycopg2):
    """
    Hook 'n wrap on `psycopg2._ext`, we modify the cursor class to our own subclass which
    overwrites execute() and executemany() to first run aikido code.
    """
    modified_psycopg2 = importhook.copy_module(psycopg2)

    aikido_cursor = generate_aikido_cursor(psycopg2._ext.cursor)

    # pylint: disable=no-member
    setattr(psycopg2._ext, "cursor", aikido_cursor)
    setattr(modified_psycopg2._ext, "cursor", aikido_cursor)
    add_wrapped_package("psycopg2")
    add_wrapped_package("psycopg2-binary")
    return modified_psycopg2
