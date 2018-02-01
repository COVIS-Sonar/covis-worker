FROM python:3.6-alpine

# Additional tools we need for alpine
RUN apk add --no-cache bash

ADD . /code
WORKDIR /code

RUN pip install -r requirements.txt

# Create non-root use
RUN adduser -u 1000 -D -g '' worker && \
    chown -R worker:worker /code
USER worker

CMD ["./wait-for-it.sh", "rabbitmq:5672", "--", "celery", "-A", "covis_worker", "worker", "-l", "info"]
