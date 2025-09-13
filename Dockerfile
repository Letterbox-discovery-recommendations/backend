FROM python:3.12-slim-trixie AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
curl ca-certificates gcc libpq-dev build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .
RUN uv build && uv pip install dist/*.whl --no-cache-dir

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--reload"]
