"""Secure PostgreSQL connection factory for ephemeral CI databases."""

import os

REQUIRED = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")


def connect_from_env():
    """Connect with psycopg using individual environment parameters.

    Never log the password or a full connection URI.
    Autocommit keeps explicit transaction blocks in full control of writes.
    """
    missing = [name for name in REQUIRED if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing PostgreSQL configuration: " + ", ".join(missing))
    import psycopg

    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=10,
        autocommit=True,
    )
