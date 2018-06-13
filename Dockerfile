FROM amarburg/covis-postprocess:latest

RUN apt-get update && apt install -yq --no-install-recommends libarchive-dev && \
      rm -rf /var/lib/apt/lists/*

# Install the local python packages
WORKDIR /root/covis-worker
ADD setup.py Makefile wait-for-it.sh ./
ADD test/data/covis_dmas.json test/data/old_covis_nas1.txt test/data/old_covis_nas6.txt ./test/data/
ADD apps/          ./apps/
ADD covis_db       ./covis_db/
ADD covis_worker/  ./covis_worker/
ADD seed_data/     ./seed_data/

RUN pip3 install -e .
