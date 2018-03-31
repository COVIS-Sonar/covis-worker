ENV BASE_IMAGE=amarburg/covis-postprocess:latest
FROM $BASE_IMAGE

# Additional tools we need for alpine
RUN apk add --no-cache bash

ADD . /root/worker
WORKDIR /root/worker

RUN pip install -r requirements.txt

# Create non-root user
#RUN adduser -u 1000 -D -g '' worker && \
#    chown -R worker:worker /code
#USER worker

ENTRYPOINT ["/root/worker/mw_python"]
CMD ["-A", "covis_worker", "worker", "-l", "info"]


#CMD ["./wait-for-it.sh", "rabbitmq:5672", "--", "celery", "-A", "covis_worker", "worker", "-l", "info"]
