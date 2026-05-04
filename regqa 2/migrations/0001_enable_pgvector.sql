-- pgvector is enabled per database, not per server, so it cannot live in the
-- image. Recording it as migration 0001 makes the dependency visible in the repo
-- and means a fresh database is set up by the same command as an existing one.
CREATE EXTENSION IF NOT EXISTS vector;
