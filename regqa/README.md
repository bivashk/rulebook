# regqa

Question answering over official documents that supersede each other. Answers cite
the source document and reflect the version in force, either now or as of a given
date.

Phase 0 is infrastructure only: no crawling, no PDFs, no retrieval yet.

## Requirements

- Docker Desktop (Windows) or Docker Engine with the compose plugin (Linux)
- [uv](https://docs.astral.sh/uv/) for running tests and migrations from your shell

`make` is optional. Every target is a one-line wrapper and the equivalent raw
command is listed below, so Windows users can skip installing it.

## First run

    cp .env.example .env        # Windows PowerShell: copy .env.example .env
    # edit .env and change POSTGRES_PASSWORD, then set the same password in DATABASE_URL

    docker compose up -d --build
    uv sync
    uv run python -m regqa.migrate
    curl http://127.0.0.1:8000/readyz

## Commands

| make            | raw command                            |
|-----------------|----------------------------------------|
| `make up`       | `docker compose up -d --build`         |
| `make down`     | `docker compose down`                  |
| `make logs`     | `docker compose logs -f api`           |
| `make migrate`  | `uv run python -m regqa.migrate`       |
| `make test`     | `uv run pytest -q`                     |
| `make lint`     | `uv run ruff check .`                  |
| `make psql`     | `docker compose exec db psql -U regqa -d regqa` |
| `make nuke`     | `docker compose down -v` (deletes data) |

## Layout

    migrations/          numbered SQL, applied in filename order
    src/regqa/config.py  every environment variable, validated at startup
    src/regqa/logging.py JSON log formatter
    src/regqa/db.py      connection pool
    src/regqa/migrate.py migration runner
    src/regqa/api/       FastAPI app
    docs/decisions/      numbered architecture decision records

## Endpoints

- `GET /healthz` — liveness. No dependencies. Used by restart policies.
- `GET /readyz` — readiness. Executes `SELECT 1`. Returns 503 within
  `READINESS_TIMEOUT_S` if the database is unreachable.
