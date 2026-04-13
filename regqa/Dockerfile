FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /app

RUN pip install --no-cache-dir uv==0.5.11

# Dependencies are installed before application code is copied, so that editing a
# source file does not invalidate the cached dependency layer on every rebuild.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src/ ./src/
COPY migrations/ ./migrations/
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uvicorn", "regqa.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
