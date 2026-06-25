import datetime as dt

from regqa.fetch.circulars import ListingRow
from regqa.fetch.runner import upsert_listing

LISTING_URL = "https://example.invalid/listing/"


def _row(**overrides) -> ListingRow:
    base = {
        "row_index": 1,
        "reference_number": "NITR/TEST/1",
        "issued_on": dt.date(2019, 7, 2),
        "title": "A test circular",
        "document_url": "https://example.invalid/docs/a.pdf",
    }
    return ListingRow(**{**base, **overrides})


def test_reinserting_the_same_row_returns_the_same_id(db):
    first, _ = upsert_listing(db, _row(), LISTING_URL)
    second, _ = upsert_listing(db, _row(), LISTING_URL)
    assert first == second


def test_same_url_and_title_but_different_date_is_a_different_row(db):
    first, _ = upsert_listing(db, _row(), LISTING_URL)
    second, _ = upsert_listing(db, _row(issued_on=dt.date(2019, 7, 3)), LISTING_URL)
    assert first != second


def test_rows_sharing_a_reference_number_are_kept_apart(db):
    # NITR/ES/2013/M/2065 is on two real documents. If the reference number were
    # any part of the key, one of them would overwrite the other.
    first, _ = upsert_listing(db, _row(document_url="https://example.invalid/a.pdf"), LISTING_URL)
    second, _ = upsert_listing(db, _row(document_url="https://example.invalid/b.pdf"), LISTING_URL)
    assert first != second


def test_null_date_rows_do_not_collapse_into_one(db):
    # Without NULLS NOT DISTINCT, Postgres treats each NULL as unequal and the
    # unique constraint silently stops working for undated rows.
    first, _ = upsert_listing(db, _row(issued_on=None), LISTING_URL)
    second, _ = upsert_listing(db, _row(issued_on=None), LISTING_URL)
    assert first == second


def test_a_new_row_has_no_document_attached(db):
    _, has_document = upsert_listing(db, _row(), LISTING_URL)
    assert has_document is False
