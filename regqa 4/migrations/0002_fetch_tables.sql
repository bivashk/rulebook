-- A file, identified by what it contains rather than where it was found. The
-- source filenames are opaque upload timestamps that do not match document dates,
-- so the URL cannot serve as identity.
CREATE TABLE raw_document (
    id               bigserial PRIMARY KEY,
    content_hash     text        NOT NULL UNIQUE,
    byte_size        bigint      NOT NULL CHECK (byte_size > 0),
    media_type       text        NOT NULL,
    storage_path     text        NOT NULL,
    first_fetched_at timestamptz NOT NULL DEFAULT now(),
    last_fetched_at  timestamptz NOT NULL DEFAULT now()
);

-- What the institute's own listing page claims about a document. This is primary
-- evidence, not navigation: the reference number and issue date appear only in
-- the HTML table and are absent from the PDF filename. Phase 3 needs to know
-- whether a date came from here or from inside the document itself.
CREATE TABLE source_listing (
    id               bigserial PRIMARY KEY,
    source           text        NOT NULL,
    listing_url      text        NOT NULL,
    document_url     text        NOT NULL,
    reference_number text,
    issued_on        date,
    title            text        NOT NULL,
    row_index        integer     NOT NULL,
    raw_document_id  bigint      REFERENCES raw_document (id),
    first_seen_at    timestamptz NOT NULL DEFAULT now(),
    last_seen_at     timestamptz NOT NULL DEFAULT now(),

    -- Reference numbers are not unique: NITR/ES/2013/M/2065 appears on two
    -- different documents. Titles repeat too. The combination below is the
    -- narrowest thing observed to distinguish rows. NULLS NOT DISTINCT is
    -- required because issued_on and reference_number are both nullable, and
    -- Postgres otherwise treats every NULL as unequal, defeating the constraint.
    UNIQUE NULLS NOT DISTINCT (source, document_url, title, issued_on)
);

CREATE INDEX source_listing_source_issued_idx ON source_listing (source, issued_on);

-- One row per invocation of the fetch command. Without this there is no way to
-- answer "did last night's crawl actually finish" after the terminal is gone.
CREATE TABLE fetch_run (
    id            bigserial PRIMARY KEY,
    source        text        NOT NULL,
    started_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz,
    rows_seen     integer     NOT NULL DEFAULT 0,
    files_fetched integer     NOT NULL DEFAULT 0,
    files_skipped integer     NOT NULL DEFAULT 0,
    failures      integer     NOT NULL DEFAULT 0
);

-- One row per URL the crawler tried. Recorded even on success, because "which
-- documents failed last night" is the first question when a run exits non-zero.
CREATE TABLE fetch_attempt (
    id           bigserial PRIMARY KEY,
    fetch_run_id bigint      NOT NULL REFERENCES fetch_run (id) ON DELETE CASCADE,
    url          text        NOT NULL,
    outcome      text        NOT NULL CHECK (outcome IN ('fetched', 'skipped', 'failed')),
    status_code  integer,
    error        text,
    attempted_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX fetch_attempt_run_idx ON fetch_attempt (fetch_run_id, outcome);
