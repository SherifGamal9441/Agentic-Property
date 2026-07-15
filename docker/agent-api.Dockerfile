FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_HTTP_TIMEOUT=120

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

EXPOSE 8002

CMD ["uv", "run", "uvicorn", "src.agent_api.app:app", "--host", "0.0.0.0", "--port", "8002"]
