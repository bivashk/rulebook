from collections.abc import Iterator
from contextlib import contextmanager

from psycopg import Connection
from psycopg_pool import ConnectionPool

from regqa.config import get_settings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    # Created on first use rather than at startup, so the api process can still
    # serve /healthz and report itself alive while the database is down.
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool(
            settings.database_url,
            min_size=1,
            max_size=settings.db_pool_max,
            timeout=settings.db_pool_timeout_s,
            open=True,
        )
    return _pool


@contextmanager
def connection(timeout: float | None = None) -> Iterator[Connection]:
    """Check out a connection. timeout overrides how long to wait for a free one.

    Callers that must answer fast, such as the readiness probe, pass a short value
    so a dead database produces a quick failure instead of a hung request.
    """
    with get_pool().connection(timeout=timeout) as conn:
        yield conn


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
