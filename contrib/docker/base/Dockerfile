FROM python:3.13

COPY --from=ghcr.io/astral-sh/uv:0.6.3 /uv /uvx /bin/
WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY contrib/docker/wait-for-it.sh wait-for-it.sh
COPY contrib/docker/docker-entrypoint.sh docker-entrypoint.sh
RUN chmod +x wait-for-it.sh \
  && chmod +x docker-entrypoint.sh \
  && mkdir docker-entrypoint.d

COPY pyproject.toml .

RUN uv sync --no-install-project

COPY . .

ENTRYPOINT ["/app/docker-entrypoint.sh"]
