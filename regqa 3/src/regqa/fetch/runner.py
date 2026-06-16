import logging
from dataclasses import dataclass
from pathlib import Path

from psycopg import Connection

from regqa.config import Settings
from regqa.fetch.circulars import LISTING_URL, ListingRow, parse_listing
from regqa.fetch.errors import DownloadError, RobotsDisallowedError
from regqa.fetch.http import PoliteClient
from regqa.fetch.storage import store

log = logging.getLogger(__name__)

SOURCE = "circulars"


@dataclass
class RunSummary:
    run_id: int
    rows_seen: int = 0
    files_fetched: int = 0
    files_skipped: int = 0
    failures: int = 0


def _start_run(conn: Connection, source: str) -> int:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO fetch_run (source) VALUES (%s) RETURNING id", (source,))
        return cur.fetchone()[0]


def _finish_run(conn: Connection, summary: RunSummary) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE fetch_run
               SET finished_at = now(), rows_seen = %s, files_fetched = %s,
                   files_skipped = %s, failures = %s
             WHERE id = %s
            """,
            (
                summary.rows_seen,
                summary.files_fetched,
                summary.files_skipped,
                summary.failures,
                summary.run_id,
            ),
        )


def _record_attempt(
    conn: Connection,
    run_id: int,
    url: str,
    outcome: str,
    status_code: int | None = None,
    error: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO fetch_attempt (fetch_run_id, url, outcome, status_code, error)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, url, outcome, status_code, error),
        )


def upsert_listing(conn: Connection, row: ListingRow, listing_url: str) -> tuple[int, bool]:
    """Insert or refresh one listing row. Returns its id and whether a file is attached."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO source_listing
                (source, listing_url, document_url, reference_number, issued_on, title, row_index)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, document_url, title, issued_on) DO UPDATE
                SET last_seen_at = now(),
                    row_index = EXCLUDED.row_index,
                    reference_number = EXCLUDED.reference_number
            RETURNING id, raw_document_id IS NOT NULL
            """,
            (
                SOURCE,
                listing_url,
                row.document_url,
                row.reference_number,
                row.issued_on,
                row.title,
                row.row_index,
            ),
        )
        listing_id, already_fetched = cur.fetchone()
        return listing_id, already_fetched


def _link_document(
    conn: Connection, listing_id: int, digest: str, size: int, media_type: str, path: Path
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_document (content_hash, byte_size, media_type, storage_path)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (content_hash) DO UPDATE SET last_fetched_at = now()
            RETURNING id
            """,
            (digest, size, media_type, str(path)),
        )
        document_id = cur.fetchone()[0]
        cur.execute(
            "UPDATE source_listing SET raw_document_id = %s WHERE id = %s",
            (document_id, listing_id),
        )


def fetch_circulars(
    conn: Connection, settings: Settings, refetch: bool = False, limit: int | None = None
) -> RunSummary:
    root = Path(settings.raw_data_dir)
    summary = RunSummary(run_id=_start_run(conn, SOURCE))
    conn.commit()

    with PoliteClient(settings.user_agent, settings.crawl_delay_s) as client:
        declared = client.crawl_delay(LISTING_URL)
        if declared is not None and declared > settings.crawl_delay_s:
            log.info("robots_crawl_delay_is_longer", extra={"declared_s": declared})

        rows = parse_listing(client.get(LISTING_URL).text, LISTING_URL)
        summary.rows_seen = len(rows)
        log.info("listing_parsed", extra={"rows": len(rows)})

        for row in rows[:limit]:
            listing_id, already_fetched = upsert_listing(conn, row, LISTING_URL)
            if already_fetched and not refetch:
                summary.files_skipped += 1
                _record_attempt(conn, summary.run_id, row.document_url, "skipped")
                conn.commit()
                continue

            try:
                response = client.get(row.document_url)
            except (DownloadError, RobotsDisallowedError) as exc:
                summary.failures += 1
                _record_attempt(
                    conn, summary.run_id, row.document_url, "failed", error=str(exc)
                )
                conn.commit()
                log.warning("fetch_failed", extra={"url": row.document_url, "error": str(exc)})
                continue

            digest, relative = store(root, response.content)
            _link_document(
                conn,
                listing_id,
                digest,
                len(response.content),
                response.headers.get("content-type", "application/pdf").split(";")[0],
                relative,
            )
            summary.files_fetched += 1
            _record_attempt(
                conn, summary.run_id, row.document_url, "fetched", response.status_code
            )
            # Committed per document so an interrupted run keeps what it already has.
            conn.commit()
            log.info("fetched", extra={"url": row.document_url, "hash": digest[:12]})

    _finish_run(conn, summary)
    conn.commit()
    return summary
