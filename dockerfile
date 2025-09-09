FROM public.ecr.aws/lambda/python:3.12

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv pip install --system -r pyproject.toml \
    && uv pip install --system -e ".[dev]"

COPY . .

ADD https://github.com/awslabs/aws-lambda-web-adapter/releases/download/v0.9.0/aws-lambda-adapter \
    /opt/extensions/aws-lambda-adapter

RUN chmod +x /opt/extensions/aws-lambda-adapter

EXPOSE 8080

CMD ["main.app"]
