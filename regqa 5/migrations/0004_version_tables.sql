-- Needed so a GiST exclusion constraint can mix an equality test on a bigint
-- with an overlap test on a range. Without it the constraint below cannot be
-- created at all.
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- A thing that has versions, as distinct from any particular file. NIT Rourkela
-- overwrites regulation PDFs in place, keeping the original filename, so for
-- regulations the URL is the stable identity and the bytes are what change.
CREATE TABLE logical_document (
    id       bigserial PRIMARY KEY,
    kind     text NOT NULL CHECK (kind IN ('regulation', 'circular')),
    identity text NOT NULL,
    title    text,
    UNIQUE (kind, identity)
);

-- Every capture the archive index reported, including the ones we rejected.
-- "We saw a capture and could not use it" is a different fact from "there was no
-- capture", and phase 6 may need to say which.
CREATE TABLE archive_snapshot (
    id                  bigserial PRIMARY KEY,
    logical_document_id bigint      NOT NULL REFERENCES logical_document (id) ON DELETE CASCADE,
    captured_at         timestamptz NOT NULL,
    original_url        text        NOT NULL,
    cdx_digest          text        NOT NULL,
    status              text        NOT NULL CHECK (status IN ('valid', 'rejected')),
    rejection_reason    text,
    raw_document_id     bigint      REFERENCES raw_document (id),
    byte_size           bigint,
    fetched_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (logical_document_id, captured_at, cdx_digest),

    -- A rejected snapshot has a reason and no file; a valid one has a file and
    -- no reason. Encoding that here stops a half-recorded row existing at all.
    CHECK ((status = 'valid'    AND raw_document_id IS NOT NULL AND rejection_reason IS NULL)
        OR (status = 'rejected' AND rejection_reason IS NOT NULL))
);

CREATE TABLE document_version (
    id                  bigserial PRIMARY KEY,
    logical_document_id bigint    NOT NULL REFERENCES logical_document (id) ON DELETE CASCADE,
    raw_document_id     bigint    NOT NULL REFERENCES raw_document (id),
    content_hash        text      NOT NULL,
    validity            daterange NOT NULL,

    -- A snapshot date is a lower bound, not the date the document changed. If a
    -- regulation was revised in June and first captured in September, September
    -- is all we know. Phase 6 has to caveat rather than assert.
    valid_from_precision text NOT NULL
        CHECK (valid_from_precision IN ('exact', 'observed_after')),

    evidence text NOT NULL
        CHECK (evidence IN ('archive_snapshot', 'listing_issue_date')),

    first_observed_at date NOT NULL,

    -- The invariant that matters: one document cannot have two versions in force
    -- on the same day. Enforced here so it is unrepresentable rather than merely
    -- tested for.
    EXCLUDE USING gist (logical_document_id WITH =, validity WITH &&)
);

CREATE INDEX document_version_validity_idx ON document_version USING gist (validity);
