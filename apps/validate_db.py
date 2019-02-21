#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json
import pathlib
import logging
import re

from pymongo import MongoClient
from decouple import config
from covis_db import db,hosts,remote,misc
from os import path

from db_validators.db_validator_main import do_validate

from minio import CopyConditions
from minio.error import ResponseError

## A good filename: 2011/10/01/APLUWCOVISMBSONAR001_20111001T030801.096Z-IMAGING.7z
##  A bad filename: 2010/10/04/APLUWCOVISMBSONAR001_20101004T121546.7z
bad_filename_re = re.compile(r'APLUWCOVISMBSONAR001_\d{8}T\d{6}\.7z')

parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')
#
# parser.add_argument('--dry-run', action='store_true')

parser.add_argument('--check-raw', action='store_true')

parser.add_argument('--fix', action='store_true')

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='INFO'),
                    help='Logging level')

## Limit of 0 mean "no limit" to limit()
parser.add_argument('--count', type=int, default=0, help='')

args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )

client = db.CovisDB(MongoClient(args.dbhost))

for run in client.runs.find({}).limit( args.count ):
    run = db.CovisRun(run, collection=client.runs)

    logging.info("Checking basename %s" % run.basename)

    if not do_validate(args,run):
        logging.error("Error running validators, skipping remaining checks")
        continue


    continue

    ## Skip validations below here for now...

    for raw in run.raw:
        if( raw.host == "DMAS" ):
            continue

        logging.info("   ... checking raw on %s : %s" % (raw.host, raw.filename))

        if not raw.accessor().exists():
            logging.info("!!! Can't find raw file on host %s" % raw.host)

            if args.fix:
                run.drop_raw(raw)
                continue

        # Check for mis-named files
        if run.site.lower() == "endeavour":
            raw_filename = path.basename(raw.filename)
            logging.info("Checking filename %s" % raw_filename)

            if re.match( bad_filename_re, raw_filename ):
                ## Know these files are all on the NAS as 7z...
                new_path = misc.make_pathname( run.basename, suffix='.7z' )

                logging.info("!!! Malformed filename %s, renaming to %s" % (raw_filename, new_path))

                if args.fix:
                    accessor = raw.accessor()
                    mclient = accessor.minio_client()

                    logging.info("Url \"%s\"; Bucket \"%s\".  Copying %s to %s", accessor.url, accessor.bucket, accessor.path, new_path)
                    try:
                        # Src path needs to include bucket name?
                        src_path = "/%s/%s" % (accessor.bucket, accessor.path)
                        #logging.info("Src path: %s" % src_path)
                        result = mclient.copy_object( accessor.bucket, new_path, src_path, CopyConditions() )
                    except ResponseError as err:
                        logging.info(err)

                    try:
                        result = mclient.remove_object( accessor.bucket, accessor.path )
                    except ResponseError as err:
                        logging.info(err)

                    result = client.runs.update_one({'basename': run.basename},
                                                        {'$pull': {"raw" : raw.json }} )
                    raw.json['filename'] = new_path
                    result = client.runs.update_one({'basename': run.basename},
                                                        {'$push': {"raw" : raw.json }} )
