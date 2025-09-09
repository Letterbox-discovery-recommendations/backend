FROM public.ecr.aws/lambda/python:3.12

COPY . .

RUN pip install uv
RUN uv sync

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

EXPOSE 8080

CMD ["app.main.handler"]
