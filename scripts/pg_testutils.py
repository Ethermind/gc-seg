"""PostgreSQL admin helpers for the test suite and the smoke test.

Both tools run against dedicated, throwaway PostgreSQL databases hosted on the
same server as development (localhost) or on the CI service container. The
functions below create (or recreate) those databases idempotently, so a fresh
clone or CI job needs zero manual setup beyond a running PostgreSQL server.
"""
from urllib.parse import urlparse, urlunparse

import psycopg
from psycopg import sql

# Maintenance database used to issue CREATE/DROP DATABASE statements.
_ADMIN_DB = "postgres"


def _split_admin(db_url: str) -> tuple[str, str]:
    """Returns (admin_connection_url, target_database_name)."""
    parts = urlparse(db_url.strip())
    db_name = parts.path.lstrip("/")
    if not db_name or "/" in db_name:
        raise ValueError(f"Database URL has no usable database name: {db_url!r}")
    admin = parts._replace(scheme="postgresql", path=f"/{_ADMIN_DB}")
    return urlunparse(admin), db_name


def ensure_database(db_url: str) -> None:
    """Creates the database named in `db_url` if it does not exist."""
    admin_url, db_name = _split_admin(db_url)
    with psycopg.connect(admin_url, autocommit=True) as conn:
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)
        ).fetchone()
        if not exists:
            conn.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
            )


def recreate_database(db_url: str) -> None:
    """Drops (if present) and recreates the database named in `db_url`.

    WITH (FORCE) terminates residual connections (requires PostgreSQL 13+).
    """
    admin_url, db_name = _split_admin(db_url)
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                sql.Identifier(db_name)
            )
        )
        conn.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
        )
