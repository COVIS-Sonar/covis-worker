from __future__ import absolute_import, unicode_literals
from .celery import app

import logging
import tempfile
import subprocess
from decouple import config

from pathlib import Path

from pycovis.postprocess import runtime

from covis_db import hosts,db

from minio import Minio

@app.task
def process(basename, destination, process_json, plot_json ):

    logging.info("Processing data from %s" % basename)

    if not destination or ("minio" not in destination):
        logger.error("No destination specified")
        return

    client = db.CovisDB()
    run = client.find_one(basename)

    if not run:
        # What's the canonical way to report errors
        logging.info("Couldn't find basename in db: %s", basename)
        return False

    # This is ugly, I'm sure there's a more Pythonic way to do it
    process_tempfile = None
    plot_tempfile = None

    ## Check if json files are existing files or JSON text
    if len(process_json) > 0 and not Path(process_json).exists:
        ## is it JSON?
        process_tempfile = tempdir.NamedTemporaryFile()
        logging.info("Saving process JSON to %s" % process_tempfile.name())
        process_tempfile.write(process_json)
        process_tempfile.sync()
        process_json = process_tempfile.name

    if len(plot_json) > 0 and not Path(plot_json).exists:
        plot_tempfile = tempdir.NameTemporaryFile()
        logging.info("Saving plot JSON to %s" % plot_tempfile.name())
        plot_tempfile.write(plot_json)
        plot_tempfile.sync()
        plot_json = plot_tempfile.name

    with tempfile.TemporaryDirectory() as workdir:

        raw = hosts.best_raw(run.raw)

        rawPath = raw.extract( workdir )

        with runtime.Runtime() as pp:
            matfile = pp.covis_imaging_sweep(rawPath, workdir, process_json)

            logging.info("Resulting matfile: %s" % matfile)

            imgfile = pp.covis_imaging_plot(matfile, workdir, plot_json)

            logging.info("Resulting plot file: %s" % imgfile)


            if "minio" in destination:
                destDir = Path(raw.filename).parent / basename

                logging.info("Saving to %s" % destDir)

                config_base = "NAS"
                access_key=config("%s_ACCESS_KEY"  % config_base )
                secret_key=config("%s_SECRET_KEY"  % config_base )
                url = config("%s_URL" % config_base )

                bucket = destination["minio"]["bucket"]

                ## Just Minio for now
                client = Minio(url,
                      access_key=access_key,
                      secret_key=secret_key,
                      secure=False)

                if not client:
                    logging.error("Unable to initialize Minio client")


                if not client.bucket_exists(bucket):
                    client.make_bucket(bucket)

                path = destDir / Path(matfile).name
                client.fput_object(bucket, str(path), matfile)

                path = destDir / Path(imgfile).name
                client.fput_object(bucket, str(path), imgfile)





    if process_tempfile:
        process_tempfile.close()

    if plot_tempfile:
        plot_tempfile.close()
