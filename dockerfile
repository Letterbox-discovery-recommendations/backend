FROM public.ecr.aws/lambda/python:3.12

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv pip install --system -r pyproject.toml \
    && uv pip install --system -e ".[dev]"

COPY . .

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

ENV PORT=8080

CMD ["main.app"]
