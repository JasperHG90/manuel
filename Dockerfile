FROM python:3.11.9-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.4.10 /uv /bin/uv

RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --all-extras

COPY src /

RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    uv sync --frozen --no-dev --all-extras

ENV PATH="/.venv/bin:$PATH"

ENV UV_PYTHON=/.venv/bin/python

ENTRYPOINT [ "uv", "run", "manuel", "run" ]
