#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json
import pathlib
import logging

from pymongo import MongoClient
from decouple import config
from covis_db import db,hosts,remote,misc

parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

parser.add_argument('--dry-run', action='store_true')

parser.add_argument('--no-check-raw', action='store_true')

parser.add_argument('--fix', action='store_true')

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='INFO'),
                    help='Logging level')

args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )

client = db.CovisDB(MongoClient(args.dbhost))

for run in client.runs.find({}):
    run = db.CovisRun(run, collection=client.runs)

    logging.info("Checking entry %s in DB" % run.basename)

    if args.no_check_raw:
        continue

    for raw in run.raw:
        if( raw.host == "DMAS" ):
            continue


        logging.info("   ... checking raw on %s : %s" % (raw.host, raw.filename))

        if not raw.accessor().exists():
            logging.info("!!! Can't find raw file on host %s" % raw.host)

            if args.fix:
                logging.info("FIX: Dropping from run")
                run.drop_raw(raw)



            # Look for a specific known problem where raw filenames
            # on covis-nas don't have the .7z extension
            if raw.host == "COVIS-NAS" and re.match(r'^(?!.*[.]7z$).*$',raw.filename):
                logging.info("!!! found file on COVIS-NAS without extention")

                if args.fix:
                    logging.info("     (fix goes here)")
