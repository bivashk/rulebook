import logging

import typer

from regqa.config import get_settings
from regqa.db import close_pool, connection
from regqa.fetch.runner import fetch_circulars
from regqa.logging import configure_logging

log = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="Corpus tooling for regqa.")
fetch_app = typer.Typer(help="Retrieve source documents.")
app.add_typer(fetch_app, name="fetch")


@fetch_app.command("circulars")
def fetch_circulars_command(
    refetch: bool = typer.Option(False, help="Download files already stored."),
    limit: int | None = typer.Option(None, help="Stop after this many listing rows."),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    try:
        with connection() as conn:
            summary = fetch_circulars(conn, settings, refetch=refetch, limit=limit)
    finally:
        close_pool()

    log.info(
        "fetch_complete",
        extra={
            "run_id": summary.run_id,
            "rows_seen": summary.rows_seen,
            "files_fetched": summary.files_fetched,
            "files_skipped": summary.files_skipped,
            "failures": summary.failures,
        },
    )
    if summary.failures:
        # A crawl that got most of the files and exited 0 is worse than one that
        # crashed, because the next phase would build on a silently short corpus.
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
