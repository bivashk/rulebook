# Rulebook: Temporal RAG QA for Institute Regulations

A question-answering system over official academic regulations, circulars, and office orders that supersede each other over time. It ensures answers reflect the rules strictly in force—either currently or as of a specific historical date—with verifiable citations back to the source document and page number.

---

## The Problem

Most institutional websites (such as universities and institutes) publish policies, circulars, and notices as individual PDFs over many years. Over time:
- A new office order partially or completely supersedes an earlier one (e.g., changes to grading criteria, attendance rules, fee structures, or hostel timings).
- Institute websites often overwrite regulation PDFs at static URLs without versioning, or keep dead links to obsolete notices.

Standard RAG systems retrieve documents purely based on semantic embedding similarity. When asked *"What is the minimum attendance required to appear for examinations?"*, a naive vector search easily retrieves and cites a 2017 circular even if an order issued in 2022 superseded it with a different requirement.

Rulebook addresses this by modeling document supersession and temporal validity directly at the database level.

---

## How It Works

1. **Ingestion & Content-Addressable Storage**: 
   Crawl institute circular listing pages. Rather than relying on unstable URLs or upload filenames, every downloaded PDF is stored content-addressed by its SHA-256 digest in `raw_document`, separate from the metadata reported on the listing page (`source_listing`).

2. **Extraction & Provenance**:
   Extract text from PDFs using PyMuPDF. If a document lacks a digital text layer (scanned circulars), the pipeline falls back to Tesseract OCR and flags the chunk with `from_ocr = true` so citation reliability is transparent. Document reference numbers, issue dates, and supersession cues (e.g., *"in supersession of office order..."*) are extracted deterministically with tested regular expressions rather than an unpredictable LLM.

3. **Temporal Modeling & Non-Overlap Invariant**:
   Document versions carry a Postgres `daterange` interval representing when they were in force. Using `btree_gist` and an exclusion constraint:
   ```sql
   EXCLUDE USING gist (logical_document_id WITH =, validity WITH &&)
   ```
   Postgres physically prevents two versions of the same document from being valid on the same calendar day.

4. **Point-in-Time Vector Retrieval**:
   Chunks are embedded with `all-MiniLM-L6-v2` (384 dimensions) into a `pgvector` column. The validity interval is denormalized directly onto each chunk and indexed with GiST. This allows historical queries (e.g., *"What was the rule as of 2021-10-15?"*) to apply temporal filtering directly in the SQL `WHERE` clause inside the vector index scan, preventing candidate loss caused by post-filtering.

---

## Repository Structure

The project was developed in iterative phases, with each phase checkpoint preserved:

- `regqa/` — **Phase 0**: Core infrastructure, Docker environment, Postgres + pgvector setup, configuration validation, structured JSON logging, and healthcheck endpoints.
- `regqa 2/` — **Phase 1 & 2**: Listing crawler, resilient HTTP fetcher, HTML table parser, and content-addressed storage.
- `regqa 3/` — **Phase 3**: PyMuPDF text extraction, Tesseract OCR fallback, and regex metadata extraction.
- `regqa 4/` — **Phase 4**: Document versioning with GiST exclusion constraints, semantic text chunking, and pgvector embeddings.
- `regqa 5/` — **Phase 5**: Consolidated SQL schema migrations.

---

## Prerequisites

- **Docker** and **Docker Compose**
- **[uv](https://docs.astral.sh/uv/)** for local Python environment and tool management
- Python 3.12+

---

## Quickstart

1. **Configure environment variables:**
   ```bash
   # In regqa/ or the active phase directory:
   export POSTGRES_USER=regqa
   export POSTGRES_PASSWORD=secretpassword
   export POSTGRES_DB=regqa
   export DATABASE_URL=postgresql://regqa:secretpassword@127.0.0.1:5432/regqa
   ```

2. **Start the database and API service:**
   ```bash
   docker compose up -d --build
   ```

3. **Install dependencies and run migrations:**
   ```bash
   uv sync
   uv run python -m regqa.migrate
   ```

4. **Verify services are ready:**
   ```bash
   curl http://127.0.0.1:8000/readyz
   ```

---

## Pipeline CLI Commands

A Typer-based CLI wraps the ingestion, extraction, and embedding pipeline:

```bash
# Crawl the institute circulars listing and download new PDFs
uv run regqa fetch circulars

# Extract text and metadata from downloaded documents
uv run regqa extract

# Fetch historical snapshots from web archives
uv run regqa fetch archive

# Construct validity intervals from issue dates and archive records
uv run regqa build-versions

# Split extracted documents into chunks
uv run regqa chunk

# Generate sentence-transformers embeddings for pending chunks
uv run regqa embed

# Run test suite
uv run pytest -q
```

---

## Key Architectural Decisions

Architectural decisions are formally tracked under `docs/decisions/` in each phase:

- **Postgres + pgvector over dedicated vector databases (ADR 0001)**: Keeps relational metadata, supersession graphs, and vector embeddings in a single ACID datastore. Allows temporal constraints (`validity @> :query_date`) to execute as a filter within the vector index scan rather than post-filtering across process boundaries.
- **Plain SQL migrations over ORM frameworks (ADR 0003)**: Migrations run in sequential order as explicit raw SQL scripts to cleanly utilize Postgres-specific extensions (`pgvector`, `btree_gist`) and exclusion constraints without ORM abstraction leaks.
- **Separation of listing rows and raw files (ADR 0004)**: Institute listing tables and actual PDF payloads have distinct lifecycles. Deduplication by SHA-256 prevents redundant storage and allows tracking dead or duplicate links cleanly.
- **Deterministic regex over LLMs for metadata extraction (ADR 0005)**: Extracts official reference numbers, dates, and supersession links via deterministic regex. This avoids LLM hallucinations, eliminates API costs, and allows every extraction edge to fail explicitly in CI if patterns drift.
