-- 384 dimensions is all-MiniLM-L6-v2. Hard-coded rather than configurable
-- because changing the model changes the column type, which is a migration, not
-- a setting: old and new vectors are not comparable and must not coexist.
CREATE TABLE chunk (
    id                  bigserial PRIMARY KEY,
    raw_document_id     bigint  NOT NULL REFERENCES raw_document (id) ON DELETE CASCADE,
    logical_document_id bigint  NOT NULL REFERENCES logical_document (id) ON DELETE CASCADE,

    ordinal    integer NOT NULL,
    page_from  integer NOT NULL,
    page_to    integer NOT NULL,
    heading    text,
    text       text    NOT NULL,
    char_count integer NOT NULL,

    -- Copied from document_version rather than joined at query time. Phase 5
    -- has to filter by date inside the vector search; a join per candidate would
    -- force post-filtering, which silently returns fewer than k results.
    validity            daterange NOT NULL,
    valid_from_precision text     NOT NULL,
    document_kind       text      NOT NULL,
    document_title      text,

    -- Provenance survives chunking. A chunk built from OCR text is less
    -- trustworthy than one from a text layer, and phase 11 needs to see that
    -- split when it explains which questions failed.
    from_ocr   boolean NOT NULL,

    embedding  vector(384),
    UNIQUE (raw_document_id, ordinal)
);

CREATE INDEX chunk_validity_idx ON chunk USING gist (validity);
CREATE INDEX chunk_pending_idx ON chunk (id) WHERE embedding IS NULL;
