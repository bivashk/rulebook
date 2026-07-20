from regqa.index.chunker import Page, split_pages

REGULATION = """4. ATTENDANCE

4.1 Every student is expected to attend all classes, tutorials and practical
sessions scheduled for the courses in which the student is registered. The
Institute considers regular attendance essential to the academic process and to
the student's own progress through the programme of study.

4.2 A student who has attended less than seventy five percent of the classes
held in a course shall be debarred from appearing in the end semester
examination of that course, and shall be awarded a grade of F irrespective of
performance in other components of assessment for that course.

4.3 The Dean Academic may condone shortage of attendance up to a limit of ten
percent on production of a medical certificate issued by the Institute Health
Centre, provided the application is made within seven days of resuming classes.
"""


def test_headings_become_chunk_boundaries():
    chunks = split_pages([Page(1, REGULATION)])
    headings = [c.heading for c in chunks if c.heading]
    assert any(h.startswith("4.2") for h in headings)
    assert any(h.startswith("4.3") for h in headings)


def test_a_rule_is_not_split_across_chunks():
    # The debarment threshold and its consequence must land in one chunk. Split
    # them and a question about either half retrieves a fragment that cannot
    # answer it.
    chunks = split_pages([Page(1, REGULATION)])
    debarment = [c for c in chunks if "seventy five percent" in c.text]
    assert len(debarment) == 1
    assert "debarred" in debarment[0].text


def test_ordinals_are_contiguous_from_zero():
    chunks = split_pages([Page(1, REGULATION)])
    assert [c.ordinal for c in chunks] == list(range(len(chunks)))


def test_page_numbers_are_carried_through():
    chunks = split_pages([Page(7, REGULATION)])
    assert all(c.page_from == 7 for c in chunks)


def test_unstructured_text_falls_back_to_size_splitting():
    # OCR output has no recoverable numbering, so chunks come out headingless.
    body = "The library will remain open during the vacation period. " * 80
    chunks = split_pages([Page(1, body)])
    assert len(chunks) > 1
    assert all(c.heading is None for c in chunks)
    assert all(c.char_count <= 1300 for c in chunks)


def test_size_split_chunks_overlap():
    body = "".join(f"Sentence number {i} about attendance rules. " for i in range(200))
    chunks = split_pages([Page(1, body)])
    assert len(chunks) > 2
    tail = chunks[0].text[-60:]
    assert any(word in chunks[1].text for word in tail.split()[:3])


def test_very_short_sections_are_merged_upward():
    text = "1. Scope\n\n" + "This regulation applies to all programmes. " * 20 + "\n1.1 Yes.\n"
    chunks = split_pages([Page(1, text)])
    assert not any(c.text.strip().endswith("1.1 Yes.") and c.char_count < 100 for c in chunks)


def test_empty_pages_are_skipped():
    assert split_pages([Page(1, ""), Page(2, "   ")]) == []


def test_a_cross_reference_mid_sentence_is_not_a_heading():
    # "as provided in 4.2 above" must not open a new chunk.
    text = "5.1 Condonation shall follow the procedure in 4.2 above and requires approval. " * 5
    chunks = split_pages([Page(1, text)])
    headings = [c.heading for c in chunks if c.heading]
    assert not any(h.startswith("4.2") for h in headings)
