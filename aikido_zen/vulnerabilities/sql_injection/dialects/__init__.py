"""
Dialects __init__.py file, imports the different dialects for quick access
"""

from aikido_zen.vulnerabilities.sql_injection.dialects.mysql import (
    SQLDialectMySQL as MySQL,
)
from aikido_zen.vulnerabilities.sql_injection.dialects.pg import (
    SQLDialectPostgres as Postgres,
)
from aikido_zen.vulnerabilities.sql_injection.dialects.sqlite import (
    SQLDialectSQLite as SQLite,
)
