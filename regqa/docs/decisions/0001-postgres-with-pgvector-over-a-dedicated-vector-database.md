# 1. Postgres with pgvector over a dedicated vector database

Status: accepted
Date: 2026-08-29

## Context

The system needs vector similarity search over document chunks, and it needs
relational data alongside it: documents, their issue and effective dates, and a
supersession graph. Retrieval must filter by "in force on date D" at query time.

## Decision

Use a single Postgres instance with the pgvector extension for both.

## Alternatives considered

- **Dedicated vector store (Qdrant, Chroma, Pinecone).** Better recall tuning and
  faster at large scale. Rejected because it means two datastores to run, back up
  and keep consistent on one cheap VPS, and because the date filter would have to
  cross a process boundary. Pinecone also has a recurring cost.
- **SQLite with a vector extension.** Smaller, but concurrent writes from a
  crawler and reads from the API are awkward, and there is no clean upgrade path.

## Consequences

- One backup, one restore, one connection string.
- The supersession filter is a WHERE clause in the same query as the vector
  search, not a post-filter (see phase 5).
- Approximate-nearest-neighbour indexes in pgvector are weaker than a purpose
  built store. At the corpus size expected here this is not the bottleneck. If it
  becomes one, that is a measurable regression, not a guess.
