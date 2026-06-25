import datetime as dt
from pathlib import Path

import pytest

from regqa.fetch.circulars import parse_listing, parse_reference
from regqa.fetch.errors import ParseError

FIXTURE = Path(__file__).parent / "fixtures" / "circulars.html"


@pytest.fixture
def rows():
    return parse_listing(FIXTURE.read_text(encoding="utf-8"))


def test_parses_every_row_with_a_link(rows):
    assert len(rows) == 5


def test_relative_links_are_made_absolute(rows):
    assert rows[0].document_url == "https://www.nitrkl.ac.in/docs/Circulars/191907190230_1.pdf"


def test_absolute_links_are_left_alone(rows):
    assert rows[1].document_url.endswith("/docs/Circulars/181501331055_1.pdf")


def test_whitespace_in_titles_is_collapsed(rows):
    assert rows[0].title == "Increase in Duration of Institute Fellowship"


def test_dates_are_parsed(rows):
    assert rows[0].issued_on == dt.date(2019, 7, 2)


def test_unparseable_date_becomes_null_rather_than_raising(rows):
    # A single malformed date should not abort a hundred-row crawl. Phase 2 can
    # recover the date from the document body.
    assert rows[4].issued_on is None


def test_placeholder_reference_becomes_null(rows):
    assert rows[1].reference_number is None


def test_reference_numbers_are_not_unique(rows):
    # Two distinct documents share NITR/ES/2013/M/2065, which is why the
    # reference number cannot be a key.
    assert rows[2].reference_number == rows[3].reference_number
    assert rows[2].title != rows[3].title


@pytest.mark.parametrize("raw", ["", "  ", "N/A", "not applicable", "NIL", "-"])
def test_absent_reference_spellings(raw):
    assert parse_reference(raw) is None


def test_missing_table_raises_with_a_useful_message():
    with pytest.raises(ParseError, match="structure has probably changed"):
        parse_listing("<html><body><p>nothing here</p></body></html>")
