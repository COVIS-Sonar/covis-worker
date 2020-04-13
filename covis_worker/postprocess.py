from __future__ import absolute_import, unicode_literals
from .celery import app

import os
import logging
import tempfile
import json
import subprocess
from decouple import config
from pyunpack import Archive

from glob import glob
from urllib.parse import urlparse
from pathlib import Path

from pymongo import MongoClient
from pycovis.postprocess import process

from covis_db import hosts,db,accessor,misc

from minio import Minio

from . import static_git_info

@app.task
def do_postprocess_run( basename, prefix = "", auto_output_path = False, force = False ):
    covis_db = db.CovisDB(MongoClient(config('MONGODB_URL',default="mongodb://localhost/")))

    run = covis_db.find(basename)

    raw = run.find_raw( "covis-nas" )
    logging.debug("Raw is %s" % raw)
    input = raw.accessor()

    output = accessor.MinioAccessor(bucket="postprocessed",
                                config_base=hosts.config_base("covis-nas"))

    return do_postprocess( input, output, prefix, auto_output_path, force )



@app.task
def do_postprocess( input, output, prefix = "", auto_output_path=False, force = False ):

    ## Check, input and output need to be a MinioAccessor (for now)
    if not isinstance( input, accessor.MinioAccessor ):
        logging.error("Input is not a MinioAccessor")
        return

    if not isinstance( output, accessor.MinioAccessor ):
        logging.error("Output is not a MinioAccessor")
        return


    prefix = Path(prefix)

    if auto_output_path:
        dest_path = prefix / misc.make_pathname( input.basename )
    else:
        dest_path = prefix / input.basename

    exists = output.exists( dest_path / (input.basename + ".mat") )

    if exists:
        if force:
            logging.warning("Output mat file exists but --force specified, recreating.")
        else:
            logging.warning("Output mat file exists ... skipping")
            return None


    tempdir = tempfile.TemporaryDirectory()
    workdir = Path(tempdir.name)

    output_path = workdir / "output"
    output_path.mkdir(exist_ok=True)

    fh = logging.FileHandler(output_path / "output.txt")
    logging.getLogger('').addHandler(fh)

    raw_archive = workdir / input.basename

    logging.info("Processing data from %s" % input.basename)

    result = input.fget_object( raw_archive  )

    if not result:
        logging.error("Couldn't get input file")
        return None

    # with runtime.Runtime() as pp:
    #     metadata = pp.postproc_metadata()

    print("Processing COVIS archive %s to path %s" % (raw_archive, output_path))

    try:
        result = process.process( raw_archive, output_path )

        for line in result.stdout:
            logging.info(line.rstrip())

    except Exception as err:
        logging.error( err  )

    metadata = process.postprocessing_metadata()
    metadata.update( static_git_info.static_git_info() )

    ## Write out metadata
    metadata_file = output_path / "metadata.json"
    logging.info("Metadata file: %s" % metadata_file)
    with open( metadata_file, 'w') as m:
        json.dump(metadata, m, indent=2)


    for output_file in os.listdir( output_path ):

        logging.debug("Copying output file: %s" % output_file)

        ## \TODO  generate correct outputName
        dest = dest_path / output_file
        dest = str(dest).strip("/")  ## Minio client doesn't like leading slash

        output.fput_object(file_path=(output_path/output_file), object_name=dest )

        logging.debug("Uploaded %s to bucket %s, path %s" % (output_file,output.bucket,dest) )

    logging.info("Finished processing %s" %  input.basename )
