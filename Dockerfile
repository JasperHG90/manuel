FROM python:3.11.9-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.4.10 /uv /bin/uv

WORKDIR /app

RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --all-extras

COPY src /app/

RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    uv sync --frozen --no-dev --all-extras

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT [ "uv", "run", "manuel", "run" ]
