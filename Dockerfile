ARG BASE_IMAGE=amarburg-latest
FROM amarburg/covis-postprocess:${BASE_IMAGE}

ADD . /root/worker
WORKDIR /root/worker

RUN apt-get update && apt-get install -y python3-pip && rm -r /var/lib/apt/lists/

RUN pip3 install -r requirements.txt

# Create non-root user
#RUN adduser -u 1000 -D -g '' worker && \
#    chown -R worker:worker /code
#USER worker

ENTRYPOINT ["/root/worker/matlab_wrapper"]
CMD ["celery", "-A", "covis_worker", "worker", "-l", "info"]


#CMD ["./wait-for-it.sh", "rabbitmq:5672", "--", "celery", "-A", "covis_worker", "worker", "-l", "info"]
