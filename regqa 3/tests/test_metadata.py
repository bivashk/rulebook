import datetime as dt

import pytest

from regqa.extract.metadata import (
    extract_page_metadata,
    find_document_number,
    find_effective,
    find_references,
    parse_date,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("01/07/2016", dt.date(2016, 7, 1)),
        ("01.11.2014", dt.date(2014, 11, 1)),
        ("1st July 2016", dt.date(2016, 7, 1)),
        ("02 Jul 2019", dt.date(2019, 7, 2)),
        ("July 2, 2019", dt.date(2019, 7, 2)),
        ("31/02/2016", None),
        ("Autumn 2018-19", None),
    ],
)
def test_parse_date(raw, expected):
    assert parse_date(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "NITR/AC/RES/2019/M/1164",
        "NITR/ES/2016/M/3400",
        "NITR/RG/BOG-61/2018/M/0574",
        "NITR/AC/Senate-72/2017/M/6083",
    ],
)
def test_finds_institute_reference_numbers(raw):
    assert find_document_number(f"Ref: {raw} dated 12 May 2019") == raw


def test_finds_ministry_reference_numbers():
    assert find_document_number("F.No.33-1/2018-TS.III") is not None


def test_effective_phrase_is_kept_even_when_it_is_not_a_date():
    # "Autumn 2018-19" is a semester. Discarding it because it will not parse
    # would throw away the document's only statement about when it applies.
    raw, parsed = find_effective("Revised Fee Structure wef Autumn 2018-19")
    assert raw == "Autumn 2018-19"
    assert parsed is None


@pytest.mark.parametrize(
    "text",
    [
        "shall take effect w.e.f. 01/07/2016",
        "shall take effect w.e.f 01/07/2016",
        "shall take effect wef 01/07/2016",
        "This order shall come into force from 01/07/2016",
        "with effect from 01/07/2016",
    ],
)
def test_effective_date_spellings(text):
    _, parsed = find_effective(text)
    assert parsed == dt.date(2016, 7, 1)


def test_supersession_cue_captures_the_target_number():
    text = (
        "In supersession of this office order no. NITR/ES/2014/M/2402 dated 28/10/2014, "
        "biometric attendance is suspended."
    )
    found = find_references(text)
    assert len(found) == 1
    assert found[0].kind == "supersedes"
    assert found[0].target_number == "NITR/ES/2014/M/2402"
    assert found[0].target_date == dt.date(2014, 10, 28)


def test_partial_modification_is_an_amendment_not_a_supersession():
    found = find_references("In partial modification of NITR/ES/2016/M/2181 dated 29/06/2016")
    assert [r.kind for r in found] == ["amends"]


def test_target_search_ignores_text_before_the_cue():
    # The document's own number appears first. Treating it as the target would
    # produce a self-referential edge in phase 3.
    text = "NITR/ES/2016/M/2220 dated 05/07/2016. In modification of NITR/ES/2016/M/2181."
    found = find_references(text)
    assert found[0].target_number == "NITR/ES/2016/M/2181"


def test_cue_without_a_target_still_records_the_mention():
    found = find_references("This circular supersedes all earlier instructions on the subject.")
    assert len(found) == 1
    assert found[0].target_number is None
    assert "earlier instructions" in found[0].context


def test_text_with_no_cues_yields_nothing():
    assert find_references("The library will remain open during the vacation.") == []


def test_page_metadata_combines_the_pieces():
    found = extract_page_metadata(
        "NITR/ES/2016/M/2220 dated 05/07/2016. In modification of NITR/ES/2016/M/2181, "
        "the holiday list is revised w.e.f. 01/07/2016."
    )
    assert found.document_number == "NITR/ES/2016/M/2220"
    assert found.effective_from == dt.date(2016, 7, 1)
    assert {r.kind for r in found.references} == {"amends"}
