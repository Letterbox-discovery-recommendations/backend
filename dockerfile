FROM python:3.12-slim AS base

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
COPY pyproject.toml uv.lock ./
RUN /root/.cargo/bin/uv sync

COPY app ./
COPY alembic.ini alembic ./
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "app.main:app", "--reload"]
