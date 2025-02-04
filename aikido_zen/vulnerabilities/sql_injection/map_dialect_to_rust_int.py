"""
Exports map_dialect_to_rust_int
"""

DIALECTS = {
    "generic": 0,
    "mysql": 8,
    "postgres": 9,
    "sqlite": 12,
}


def map_dialect_to_rust_int(dialect):
    """
    This takes the string dialect as input and maps it to a rust integer
    Reference : [rust lib]/src/sql_injection/helpers/select_dialect_based_on_enum.rs
    """
    return DIALECTS[dialect]
