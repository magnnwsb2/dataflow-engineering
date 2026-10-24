"""Apply the versioned PostgreSQL schema within a transaction.

A live PostgreSQL connection is provided by the caller. This module never
creates databases or stores passwords. Integration tests are pending.
"""

from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "sql" / "001_initial_schema.sql"


def schema_sql() -> str:
    """Return the checked-in schema; fail explicitly if it is missing."""
    return SCHEMA_PATH.read_text(encoding="utf-8")


def apply_schema(connection: Any) -> None:
    """Apply schema atomically using a caller-provided psycopg connection."""
    with connection.transaction():
        connection.execute(schema_sql())
