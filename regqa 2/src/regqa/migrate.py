import logging
import sys
from pathlib import Path

from psycopg import Connection

from regqa.config import get_settings
from regqa.db import close_pool, connection
from regqa.logging import configure_logging

log = logging.getLogger(__name__)

# Resolved against the working directory: the repo root on your machine, /app in
# the container. Both have a migrations/ directory at that location.
MIGRATIONS_DIR = Path("migrations")

_BOOTSTRAP = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
)
"""


class MigrationError(RuntimeError):
    pass


def discover(directory: Path = MIGRATIONS_DIR) -> list[Path]:
    if not directory.is_dir():
        raise MigrationError(f"migrations directory not found: {directory.resolve()}")
    return sorted(directory.glob("*.sql"))


def applied_versions(conn: Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def apply_all(conn: Connection, directory: Path = MIGRATIONS_DIR) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(_BOOTSTRAP)
    conn.commit()

    done = applied_versions(conn)
    newly_applied: list[str] = []

    for path in discover(directory):
        if path.stem in done:
            continue
        # One transaction per file. A half-applied migration is worse than a failed
        # one, because the next run would record it as done and skip the remainder.
        with conn.transaction(), conn.cursor() as cur:
            cur.execute(path.read_text(encoding="utf-8"))
            cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
        log.info("migration_applied", extra={"version": path.stem})
        newly_applied.append(path.stem)

    return newly_applied


def main() -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    try:
        with connection() as conn:
            applied = apply_all(conn)
        log.info("migrate_complete", extra={"applied": applied, "count": len(applied)})
    finally:
        # Pool worker threads are non-daemon. Without an explicit close the
        # interpreter blocks five seconds per thread before it can exit.
        close_pool()
    return 0


if __name__ == "__main__":
    sys.exit(main())
