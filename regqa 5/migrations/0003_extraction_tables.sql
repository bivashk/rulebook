-- One row per page rather than one blob per document. Phase 4 chunks within
-- pages, and a citation that says "page 3 of this notice" is worth more to a
-- reader than one pointing at a whole document.
CREATE TABLE document_page (
    id              bigserial PRIMARY KEY,
    raw_document_id bigint      NOT NULL REFERENCES raw_document (id) ON DELETE CASCADE,
    page_number     integer     NOT NULL CHECK (page_number > 0),
    text            text        NOT NULL,
    char_count      integer     NOT NULL,

    -- Provenance, not decoration. If evaluation in phase 11 shows a class of
    -- questions failing, the first thing to check is whether the underlying
    -- text was read or guessed at by an OCR engine.
    text_source     text        NOT NULL CHECK (text_source IN ('text_layer', 'ocr', 'empty')),
    ocr_confidence  real,

    extracted_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (raw_document_id, page_number)
);

CREATE INDEX document_page_source_idx ON document_page (text_source);

-- Fields pulled out of the document body. Every column is nullable because a
-- null here is a finding: it means the pattern did not match, which is a fact
-- about the corpus that phase 3 needs to reason about.
CREATE TABLE document_metadata (
    raw_document_id bigint PRIMARY KEY REFERENCES raw_document (id) ON DELETE CASCADE,
    document_number text,
    issued_on       date,
    effective_from  date,

    -- Kept verbatim alongside the parsed date because effective dates are not
    -- always dates. "wef Autumn 2018-19" names a semester, and resolving it
    -- needs the academic calendar, which is a later problem.
    effective_raw   text,

    page_count      integer     NOT NULL,
    extracted_at    timestamptz NOT NULL DEFAULT now()
);

-- A mention, in one document, of another document. Deliberately not an edge:
-- an edge asserts a relationship, and phase 3 decides which of these are strong
-- enough to become one. Storing the cue and its surrounding text means that
-- decision can be reviewed against the actual words.
CREATE TABLE extracted_reference (
    id              bigserial PRIMARY KEY,
    raw_document_id bigint  NOT NULL REFERENCES raw_document (id) ON DELETE CASCADE,
    page_number     integer NOT NULL,
    kind            text    NOT NULL CHECK (kind IN
                        ('supersedes', 'amends', 'cancels', 'continues', 'references')),
    cue_text        text    NOT NULL,
    context         text    NOT NULL,
    target_number   text,
    target_date     date
);

CREATE INDEX extracted_reference_document_idx ON extracted_reference (raw_document_id, kind);
CREATE INDEX extracted_reference_target_idx ON extracted_reference (target_number)
    WHERE target_number IS NOT NULL;
