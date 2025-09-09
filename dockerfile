FROM python:3.12-slim-trixie AS base
FROM ghcr.io/astral-sh/uv:latest AS uvstage

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

COPY --from=uvstage /uv /bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY app ./
COPY alembic.ini alembic ./
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "app.main:app", "--reload"]
