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

    exists = output.exists( dest_path / "metadata.json" )

    if exists:
      logging.info("Output metadata file exists")
      if not force:
        logging.info(" ... skipping")
        return None


    tempdir = tempfile.TemporaryDirectory()
    workdir = Path(tempdir.name)

    output_path = workdir / "output"
    output_path.mkdir(exist_ok=True)

    raw_archive = workdir / input.basename

    logging.info("Processing data from %s" % input)

    result = input.fget_object( raw_archive  )

    if not result:
        logging.error("Couldn't get input file")
        return None

    # with runtime.Runtime() as pp:
    #     metadata = pp.postproc_metadata()

    print("Processing COVIS archive %s to path %s" % (raw_archive, output_path))

    process.process( raw_archive, output_path )
    metadata = process.postprocessing_metadata()

    ## Add metadata about the covis-worker process
    static_git_info.add_static_git_info( metadata )

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



    # input = urlparse(inputURL)
    # output = urlparse(outputURL)
    #
    # ## Validate output before starting
    # outputMinioClient = None
    #
    # ## Validate the output first, rather than catch it at the end
    # if output.scheme == '':
    #     ## If writing to file, work directly in the final destination
    #     output_path = Path(output.path)
    #
    # elif output.scheme == 's3':
    #     s3host = config('OUTPUT_S3_HOST', default="")
    #     if not s3host:
    #         logging.warning("s3:// output URL provided but OUTPUT_S3_HOST not provided")
    #         return
    #
    #     outputMinioClient = Minio(s3host,
    #                   access_key=config('OUTPUT_S3_ACCESS_KEY', default=""),
    #                   secret_key=config('OUTPUT_S3_SECRET_KEY', default=""),
    #                   secure=False)
    #
    #
    # ## If not otherwise set while validating output options
    # if not output_path:
    #     output_path = workdir / "output"
    #     output_path.mkdir(exist_ok=True)
    #
    #
    #
    # if input.scheme == '':
    #     rawArchive = Path(args.inputFile).resolve()
    #
    #     #rawPath = uncompressCovisData(inputPath,workdir)
    #
    # elif input.scheme == 's3':
    #     s3host = config('RAW_S3_HOST', default="")
    #     if not s3host:
    #         sys.exit("s3:// input URL provided but RAW_S3_HOST not provided")
    #
    #     bucket = input.netloc
    #     path   = input.path
    #
    #     print("Retrieving bucket: %s, path %s from host %s" % (bucket, path, s3host))
    #
    #     minioClient = Minio(s3host,
    #                   access_key=config('RAW_S3_ACCESS_KEY', default=""),
    #                   secret_key=config('RAW_S3_SECRET_KEY', default=""),
    #                   secure=False)
    #
    #     basename = Path(path).name
    #     rawArchive = workdir / basename
    #
    #     print("Retrieving path %s from bucket %s to %s" % (path, bucket, rawArchive))
    #
    #     minioClient.fget_object(bucket_name=bucket, object_name=path, file_path= str(rawArchive) )
    #
    #     #rawPath = uncompressCovisData(downloadDest, workdir)
    #
    # elif input.scheme == 'db':
    #
    # # # Validate destination before Processing
    # # if "minio" in destination:
    # #     mdest = destination["minio"]
    # #     if "host" not in mdest or not hosts.validate_host(mdest["host"]):
    # #         logger.error("Invalid host specified for minio destination")
    # #         return False
    # #
    # #     valid = True
    # #
    #     client = db.CovisDB()
    #     run = client.find_one(basename)
    #
    #     if not run:
    #         # What's the canonical way to report errors
    #         logging.info("Couldn't find basename in db: %s", basename)
    #         return False
    #
    #     raw = hosts.best_raw(run.raw)
    #     rawPath = raw.extract( workdir )
    #
    # # # This is ugly, I'm sure there's a more Pythonic way to do it
    # # process_tempfile = None
    # # plot_tempfile = None
    # #
    # # ## Check if json files are existing files or JSON text
    # # if len(process_json) > 0 and not Path(process_json).exists:
    # #     ## is it JSON?
    # #     process_tempfile = tempdir.NamedTemporaryFile()
    # #     logging.info("Saving process JSON to %s" % process_tempfile.name())
    # #     process_tempfile.write(process_json)
    # #     process_tempfile.sync()
    # #     process_json = process_tempfile.name
    # #
    # # if len(plot_json) > 0 and not Path(plot_json).exists:
    # #     plot_tempfile = tempdir.NameTemporaryFile()
    # #     logging.info("Saving plot JSON to %s" % plot_tempfile.name())
    # #     plot_tempfile.write(plot_json)
    # #     plot_tempfile.sync()
    # #     plot_json = plot_tempfile.name
    #
    #
    # if not rawArchive:
    #     logging.error("Could not find input file")
    #     return
    #
    #
    #
    # # with runtime.Runtime() as pp:
    # #     metadata = pp.postproc_metadata()
    #
    # print("Processing COVIS archive %s to path %s" % (rawArchive, output_path))
    #
    # process.process( rawArchive, output_path )
    #
    # metadata = process.postprocessing_metadata()
    #
    # ## Add metadata about the covis-worker process
    # static_git_info.add_static_git_info( metadata )
    #
    # ## Write out metadata
    # metadata_file = output_path / "metadata.json"
    # logging.info("Metadata file: %s" % metadata_file)
    # with open( metadata_file, 'w') as m:
    #     json.dump(metadata, m, indent=2)
    #
    #
    # if outputMinioClient:
    #     ## Upload to Minio
    #
    #     outbucket = output.netloc
    #
    #     if not outputMinioClient.bucket_exists( outbucket ):
    #         outputMinioClient.make_bucket(outbucket)
    #
    #
    #     print("Results in output_path:")
    #
    #     for output_file in os.listdir( output_path ):
    #
    #         print("output_file: %s" % output_file)
    #
    #         ## \TODO  generate correct outputName
    #         outpath = Path(output.path) / output_file
    #         outpath = str(outpath).strip("/")  ## Minio client doesn't like leading slash
    #
    #         outputMinioClient.fput_object(file_path=(output_path/output_file), bucket_name=outbucket, object_name=outpath)
    #
    #         print("Uploaded %s to bucket %s, path %s" % (output_file,outbucket,outpath) )
