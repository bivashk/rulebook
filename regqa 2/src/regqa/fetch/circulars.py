import datetime as dt
import logging
import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from regqa.fetch.errors import ParseError

log = logging.getLogger(__name__)

LISTING_URL = "https://www.nitrkl.ac.in/FacultyStaff/CircularNotices/"

# Values the institute uses in the reference column to mean "there isn't one".
_ABSENT_REFERENCE = frozenset({"", "-", "na", "n/a", "not applicable", "nil"})

_DATE_FORMATS = ("%d %b %Y", "%d %B %Y", "%d-%m-%Y", "%d/%m/%Y")


@dataclass(frozen=True)
class ListingRow:
    row_index: int
    reference_number: str | None
    issued_on: dt.date | None
    title: str
    document_url: str


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_date(raw: str) -> dt.date | None:
    value = _clean(raw)
    for fmt in _DATE_FORMATS:
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_reference(raw: str) -> str | None:
    value = _clean(raw)
    return None if value.lower() in _ABSENT_REFERENCE else value


def _find_listing_table(soup: BeautifulSoup) -> Tag:
    """Locate the circulars table by its header text rather than by position.

    Selecting on a CSS class or nth-table would break the first time the page's
    template changes. The header words are the thing least likely to move.
    """
    for table in soup.find_all("table"):
        header = _clean(table.get_text(" ", strip=True)[:400]).lower()
        if "reference" in header and "title" in header:
            return table
    raise ParseError(
        "no table containing both 'reference' and 'title' headers was found; "
        "the listing page structure has probably changed"
    )


def parse_listing(html: str, base_url: str = LISTING_URL) -> list[ListingRow]:
    soup = BeautifulSoup(html, "lxml")
    table = _find_listing_table(soup)

    rows: list[ListingRow] = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 5:
            continue  # header rows carry <th>, not <td>

        link = cells[4].find("a", href=True)
        if link is None:
            log.warning("listing_row_without_link", extra={"title": _clean(cells[3].get_text())})
            continue

        rows.append(
            ListingRow(
                row_index=int(_clean(cells[0].get_text()) or len(rows) + 1),
                reference_number=parse_reference(cells[1].get_text()),
                issued_on=parse_date(cells[2].get_text()),
                title=_clean(cells[3].get_text()),
                document_url=urljoin(base_url, link["href"]),
            )
        )

    if not rows:
        raise ParseError("listing table was found but contained no parseable rows")
    return rows
