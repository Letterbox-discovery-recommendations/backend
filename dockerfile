FROM public.ecr.aws/lambda/python:3.11

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

# Descargar el adapter Raro que me dijo seba
ADD https://github.com/awslabs/aws-lambda-web-adapter/releases/latest/download/aws-lambda-adapter \
    /opt/extensions/aws-lambda-adapter
RUN chmod +x /opt/extensions/aws-lambda-adapter

ENV AWS_LWA_PORT=8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
