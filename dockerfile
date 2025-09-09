FROM public.ecr.aws/lambda/python:3.12

RUN yum install -y postgresql-devel gcc python3-devel make && yum clean all

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY . .

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

EXPOSE 8080

CMD ["app.main.handler"]
