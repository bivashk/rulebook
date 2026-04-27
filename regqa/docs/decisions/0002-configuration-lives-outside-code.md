# 2. Configuration lives outside code

Status: accepted
Date: 2026-08-29

## Context

The same image must run on a laptop, on a VPS and in CI, with different database
hosts and different secrets.

## Decision

All configuration comes from environment variables, parsed by a single
pydantic-settings `Settings` class. `.env` is gitignored; `.env.example` is
committed and lists every variable.

## Consequences

- Secrets have no defaults. A missing `DATABASE_URL` raises a validation error at
  startup rather than surfacing as a confusing failure mid-run.
- Values are type-coerced and validated once, at the boundary.
- Rebuilding the image is not required to change an environment.
