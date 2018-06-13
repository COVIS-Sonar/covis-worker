FROM golang:stretch

# Derived from the Alpine-based Minio image
LABEL maintainer="Minio Inc <dev@minio.io>"

ENV GOPATH /go
ENV PATH $PATH:$GOPATH/bin
ENV CGO_ENABLED 0
ENV MINIO_UPDATE off
ENV MINIO_ACCESS_KEY_FILE=access_key \
    MINIO_SECRET_KEY_FILE=secret_key

WORKDIR /go/src/github.com/minio/

COPY dockerscripts/docker-entrypoint.sh dockerscripts/healthcheck.sh /usr/bin/
RUN chmod 755 /usr/bin/docker-entrypoint.sh /usr/bin/healthcheck.sh

RUN  \
    apt -yqq update && \
    apt install -yq --no-install-recommends ca-certificates curl git && \
    curl -sL https://deb.nodesource.com/setup_8.x | bash - && \
    apt install -yq nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    echo 'hosts: files mdns4_minimal [NOTFOUND=return] dns mdns4' >> /etc/nsswitch.conf && \
    go get -v -d github.com/minio/minio && \
    cd /go/src/github.com/minio/minio && \
    go install -v -ldflags "$(go run buildscripts/gen-ldflags.go)" && \
    rm -rf /go/pkg /go/src /usr/local/go


EXPOSE 9000

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]

HEALTHCHECK --interval=30s --timeout=5s \
    CMD /usr/bin/healthcheck.sh

## Install dat
RUN npm install -g dat

## Get test data
ENV DAT_URL dat://8dc8f4eb4b51d286f3ed4d825016a27ca5888e24cb4fffca019c740acf01c2e4
RUN dat clone ${DAT_URL} /data
