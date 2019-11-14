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

from pycovis.postprocess import process

from covis_db import hosts,db

from minio import Minio

from . import static_git_info

@app.task
def do_postprocess(inputURL, outputURL, autoOutputPath=False ):

            # job_prefix = None,
            # process_json = None,
            # plot_json = None):

    tempdir = tempfile.TemporaryDirectory()
    workdir = Path(tempdir.name)

    logging.info("Processing data from %s" % inputURL)

    outputPath = None

    input = urlparse(inputURL)
    output = urlparse(outputURL)

    ## Validate output before starting
    outputMinioClient = None

    ## Validate the output first, rather than catch it at the end
    if output.scheme == '':
        ## If writing to file, work directly in the final destination
        outputPath = Path(output.path)

    elif output.scheme == 's3':
        s3host = config('OUTPUT_S3_HOST', default="")
        if not s3host:
            logging.warning("s3:// output URL provided but OUTPUT_S3_HOST not provided")
            return

        outputMinioClient = Minio(s3host,
                      access_key=config('OUTPUT_S3_ACCESS_KEY', default=""),
                      secret_key=config('OUTPUT_S3_SECRET_KEY', default=""),
                      secure=False)


    ## If not otherwise set while validating output options
    if not outputPath:
        outputPath = workdir / "output"
        outputPath.mkdir(exist_ok=True)



    if input.scheme == '':
        rawArchive = Path(args.inputFile).resolve()

        #rawPath = uncompressCovisData(inputPath,workdir)

    elif input.scheme == 's3':
        s3host = config('RAW_S3_HOST', default="")
        if not s3host:
            sys.exit("s3:// input URL provided but RAW_S3_HOST not provided")

        bucket = input.netloc
        path   = input.path

        print("Retrieving bucket: %s, path %s from host %s" % (bucket, path, s3host))

        minioClient = Minio(s3host,
                      access_key=config('RAW_S3_ACCESS_KEY', default=""),
                      secret_key=config('RAW_S3_SECRET_KEY', default=""),
                      secure=False)

        basename = Path(path).name
        rawArchive = workdir / basename

        print("Retrieving path %s from bucket %s to %s" % (path, bucket, rawArchive))

        minioClient.fget_object(bucket_name=bucket, object_name=path, file_path= str(rawArchive) )

        #rawPath = uncompressCovisData(downloadDest, workdir)

    elif input.scheme == 'db':

    # # Validate destination before Processing
    # if "minio" in destination:
    #     mdest = destination["minio"]
    #     if "host" not in mdest or not hosts.validate_host(mdest["host"]):
    #         logger.error("Invalid host specified for minio destination")
    #         return False
    #
    #     valid = True
    #
        client = db.CovisDB()
        run = client.find_one(basename)

        if not run:
            # What's the canonical way to report errors
            logging.info("Couldn't find basename in db: %s", basename)
            return False

        raw = hosts.best_raw(run.raw)
        rawPath = raw.extract( workdir )

    # # This is ugly, I'm sure there's a more Pythonic way to do it
    # process_tempfile = None
    # plot_tempfile = None
    #
    # ## Check if json files are existing files or JSON text
    # if len(process_json) > 0 and not Path(process_json).exists:
    #     ## is it JSON?
    #     process_tempfile = tempdir.NamedTemporaryFile()
    #     logging.info("Saving process JSON to %s" % process_tempfile.name())
    #     process_tempfile.write(process_json)
    #     process_tempfile.sync()
    #     process_json = process_tempfile.name
    #
    # if len(plot_json) > 0 and not Path(plot_json).exists:
    #     plot_tempfile = tempdir.NameTemporaryFile()
    #     logging.info("Saving plot JSON to %s" % plot_tempfile.name())
    #     plot_tempfile.write(plot_json)
    #     plot_tempfile.sync()
    #     plot_json = plot_tempfile.name


    if not rawArchive:
        logging.error("Could not find input file")
        return



    # with runtime.Runtime() as pp:
    #     metadata = pp.postproc_metadata()

    print("Processing COVIS archive %s to path %s" % (rawArchive, outputPath))

    process.process( rawArchive, outputPath )

    metadata = process.postprocessing_metadata()

    ## Add metadata about the covis-worker process
    static_git_info.add_static_git_info( metadata )

    ## Write out metadata
    metadata_file = outputPath / "metadata.json"
    logging.info("Metadata file: %s" % metadata_file)
    with open( metadata_file, 'w') as m:
        json.dump(metadata, m, indent=2)


    if outputMinioClient:
        ## Upload to Minio

        outbucket = output.netloc

        if not outputMinioClient.bucket_exists( outbucket ):
            outputMinioClient.make_bucket(outbucket)


        print("Results in outputPath:")

        for outputFile in os.listdir( outputPath ):

            print("Outputfile: %s" % outputFile)

            ## \TODO  generate correct outputName
            outpath = Path(output.path) / outputFile
            outpath = str(outpath).strip("/")  ## Minio client doesn't like leading slash

            outputMinioClient.fput_object(file_path=(outputPath/outputFile), bucket_name=outbucket, object_name=outpath)

            print("Uploaded %s to bucket %s, path %s" % (outputFile,outbucket,outpath) )


    # matfile = None
    # if process_json:
    #     logging.debug("Using process JSON file %s" % process_json)
    #     matfile = pp.covis_process_sweep(rawPath, workdir, 'json_file', process_json)
    # else:
    #     logging.debug("Using process JSON file %s" % process_json)
    #     matfile = pp.covis_process_sweep(rawPath, workdir)
    #
    # logging.info("Resulting matfile: %s" % matfile)
    #
    # imgfile = None
    # if plot_json:
    #     logging.debug("Using plot JSON file %s" % plot_json)
    #     imgfile = pp.covis_plot_sweep(matfile, workdir, 'json_file', plot_json)
    # else:
    #     logging.debug("Using plot JSON file %s" % plot_json)
    #     imgfile = pp.covis_plot_sweep(matfile, workdir)
    #
    # logging.info("Resulting plot file: %s" % imgfile)

            #

            #
            # if "minio" in destination:
            #
            #     # Rebuild new pathname based on date
            #     # TODO: Should move this to a function
            #     destDir = Path(run.datetime.strftime("%Y/%m/%d/")) / basename
            #
            #
            #     destDir = Path(job_prefix) / destDir
            #
            #     logging.info("Saving to %s" % destDir )
            #
            #     config_base = hosts.config_base( destination["minio"]["host"] )
            #     access_key=config("%s_ACCESS_KEY"  % config_base )
            #     secret_key=config("%s_SECRET_KEY"  % config_base )
            #     url = config("%s_URL" % config_base )
            #
            #     bucket = destination["minio"]["bucket"]
            #
            #     ## Just Minio for now
            #     client = Minio(url,
            #           access_key=access_key,
            #           secret_key=secret_key,
            #           secure=False)
            #
            #     if not client:
            #         logging.error("Unable to initialize Minio client")
            #
            #
            #     if not client.bucket_exists(bucket):
            #         client.make_bucket(bucket)
            #
            #     path = destDir / Path(matfile).name
            #     client.fput_object(bucket, str(path), matfile)
            #
            #     path = destDir / Path(imgfile).name
            #     client.fput_object(bucket, str(path), imgfile)
            #
            #     path = destDir / "metadata.json"
            #     client.fput_object(bucket, str(path), metadata_file)
            #
            #
            #


    # if process_tempfile:
    #     process_tempfile.close()
    #
    # if plot_tempfile:
    #     plot_tempfile.close()


## Takes path to a COVIS data archive (.tar.gz or .7z format) and a temporary
## directory to unpack the data into.
##
## Returns a path to the unpacked COVIS data
# def uncompressCovisData( inputPath, tempdir ):
#     ## Unpack archive in Python
#     Archive(inputPath).extractall( tempdir )
#
#     ## \TODO  Need a way to find the directory name found in the archive rather
#     ## than this open-loop version
#     for p in Path(tempdir).rglob("*/"):
#         print(p)
#         if p.is_dir():
#             print("Returning %s" % p)
#             return p
#
#     return None
