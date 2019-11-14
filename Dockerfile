FROM amarburg/covis-postprocess:latest

## For speed when building _this_ image, any .deb packages
## should be added in postprocessing/Deploy/Dockerfile
#RUN apt-get update && apt install -yq --no-install-recommends \
#                            libarchive-dev netcat p7zip-full && \
#      rm -rf /var/lib/apt/lists/*

# Pre-install dependencies by hand so they get cached in an earlier
#     Docker layer
RUN pip3 install --upgrade celery flower minio pymongo libarchive \
            python-decouple requests boto3 paramiko

# Install the local python packages

WORKDIR /home/covis/covis-worker
USER root
RUN chown covis:covis /home/covis/covis-worker

USER covis
COPY --chown=covis:covis  setup.py Makefile wait-for-it.sh ./
COPY --chown=covis:covis  apps/          ./apps/
COPY --chown=covis:covis  covis_db/      ./covis_db/
COPY --chown=covis:covis  covis_worker/  ./covis_worker/
COPY --chown=covis:covis  seed_data/seed_data.bson ./

## Make input/ directory local to working directory.
#RUN ln -s /home/covis/input .

RUN pip3 install -e .

ENV LD_LIBRARY_PATH=$MATLAB_LD_LIBRARY_PATH

## Add ~/.local/bin as that's where pip-installed cmds end up
ENV PATH=/home/covis/.local/bin:${PATH}

ENTRYPOINT []
CMD ["make", "worker"]
