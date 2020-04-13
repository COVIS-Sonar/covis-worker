#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json
import logging

from pymongo import MongoClient
from bson import json_util
from decouple import config
from covis_db import db, hosts
from datetime import datetime


from covis_worker import postprocess


parser = argparse.ArgumentParser()

# parser.add_argument('--config', default=config('PROCESS_CONFIG',""),
#                     help="Process.json files.  Can be a path, URL, or '-' for stdin")

parser.add_argument('--dbhost', default=config('MONGODB_URL',
                    default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='INFO'),
                    help='Logging level')

parser.add_argument('--prefix', nargs='?', default=config('POSTPROC_PREFIX', default=""),
                    help='Prefix appended to output filename')

parser.add_argument('--count', default=0, type=int,
                    metavar='N',
                    help="Only queue N entries (used for debugging)")

parser.add_argument('--dry-run', dest='dryrun', action='store_true')

parser.add_argument("--run-local", dest='runlocal', action='store_true')

parser.add_argument("--force", dest='force', action='store_true')

# parser.add_argument("--output",  help="URL for output",
#                         dest="outputDir", default="/output")
#
# parser.add_argument("--auto-output-path", action='store_true', dest="autoOutputPath",
#                     help="Automatically add the YYYY/MM/DD/ path to the output")

parser.add_argument('basenames', nargs='*')

parser.add_argument("--regex", nargs="*", default=[], help="Regex for basenames to process")

args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )

client = db.CovisDB(MongoClient(args.dbhost))

basenames = args.basenames

for reg in args.regex:
    basenames.extend( [run.basename for run in client.find_regex(reg)] )

logging.info("Checking %d basenames" % len(basenames))
logging.debug("Checking these basenames: %s" % basenames)

## Validate existence of each basename
validated_basenames = []
for basename in basenames:
    if client.find( basename ):
        validated_basenames.append(basename)
    else:
        logging.warning("Unable to find basename, skipping: %s" % basename )

logging.info("Post-processing %d validated basenames" % len(basenames))
logging.debug("Validated basenames: %s" % basenames)

## If specified, load the JSON configuration
for basename in validated_basenames:

    if not args.dryrun:

        if args.runlocal:
            job = postprocess.do_postprocess_run( basename, prefix=args.prefix,
                                    auto_output_path = True, force=args.force )

        else:
            job = postprocess.do_postprocess_run.delay( basename, prefix=args.prefix,
                                    auto_output_path = True, force=args.force )


    else:
        logging.warning("Dry run, skipping...")
