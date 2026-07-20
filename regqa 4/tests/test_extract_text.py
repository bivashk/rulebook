import pymupdf
import pytest

from regqa.extract.errors import UnreadablePdfError
from regqa.extract.text import extract_pages, ocr_available

SENTENCE = (
    "In supersession of office order NITR/ES/2014/M/2402 dated 28/10/2014, "
    "biometric attendance stands suspended with effect from 01/12/2016."
)


def _text_pdf(path, body=SENTENCE, pages=1):
    document = pymupdf.open()
    for _ in range(pages):
        page = document.new_page()
        page.insert_textbox(pymupdf.Rect(40, 40, 550, 700), body, fontsize=11)
    document.save(path)
    document.close()
    return path


def _scanned_pdf(path, body=SENTENCE):
    """A PDF whose only content is a picture of text, with no text layer."""
    source = pymupdf.open()
    page = source.new_page()
    page.insert_textbox(pymupdf.Rect(40, 40, 550, 700), body, fontsize=22)
    pixmap = page.get_pixmap(dpi=200)
    source.close()

    document = pymupdf.open()
    target = document.new_page(width=pixmap.width * 0.75, height=pixmap.height * 0.75)
    target.insert_image(target.rect, pixmap=pixmap)
    document.save(path)
    document.close()
    return path


def test_text_layer_is_used_when_present(tmp_path):
    pages = extract_pages(_text_pdf(tmp_path / "text.pdf"))
    assert len(pages) == 1
    assert pages[0].source == "text_layer"
    assert "NITR/ES/2014/M/2402" in pages[0].text


def test_every_page_is_returned_in_order(tmp_path):
    pages = extract_pages(_text_pdf(tmp_path / "three.pdf", pages=3))
    assert [p.page_number for p in pages] == [1, 2, 3]


def test_a_corrupt_file_raises_rather_than_returning_nothing(tmp_path):
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 this is not a pdf")
    with pytest.raises(UnreadablePdfError):
        extract_pages(broken)


@pytest.mark.skipif(not ocr_available(), reason="tesseract is not installed")
def test_scanned_page_falls_back_to_ocr(tmp_path):
    pages = extract_pages(_scanned_pdf(tmp_path / "scan.pdf"))
    assert pages[0].source == "ocr"
    assert pages[0].ocr_confidence is not None
    assert "NITR" in pages[0].text


@pytest.mark.skipif(not ocr_available(), reason="tesseract is not installed")
def test_ocr_recovers_the_reference_number_from_an_image(tmp_path):
    from regqa.extract.metadata import extract_page_metadata

    pages = extract_pages(_scanned_pdf(tmp_path / "scan2.pdf"))
    found = extract_page_metadata(pages[0].text)
    assert found.document_number is not None
    assert found.document_number.startswith("NITR")
