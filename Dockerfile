FROM amarburg/covis-postprocess:latest

RUN apt-get update && apt install -yq --no-install-recommends \
                            libarchive-dev netcat p7zip-full && \
      rm -rf /var/lib/apt/lists/*

## Install dependencies by hand so they get cached by Docker!
RUN pip3 install celery flower minio pymongo libarchive python-decouple

# Install the local python packages
WORKDIR /root/covis-worker
ADD setup.py Makefile wait-for-it.sh ./
ADD apps/          ./apps/
ADD covis_db/      ./covis_db/
ADD covis_worker/  ./covis_worker/
ADD seed_data/seed_data.bson ./

## Make input/ directory local to working directory.
RUN ln -s ~/input .

RUN pip3 install -e .

ENTRYPOINT ["make", "worker"]
