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

# parser.add_argument('--dest-host', dest="desthost", default="COVIS-NAS",
#                     help='Destination host')

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='INFO'),
                    help='Logging level')

parser.add_argument('--job', metavar='log', nargs='?',
                    help='Job name')

parser.add_argument('--count', default=0, type=int,
                    metavar='N',
                    help="Only queue N entries (used for debugging)")

parser.add_argument('--dry-run', dest='dryrun', action='store_true')

parser.add_argument("--run-local", dest='runlocal', action='store_true')

parser.add_argument("--output",  help="URL for output",
                        dest="outputDir", default="/output")

parser.add_argument("--auto-output-path", action='store_true', dest="autoOutputPath",
                    help="Automatically add the YYYY/MM/DD/ path to the output")

parser.add_argument('inputs', nargs='*')

# parser.add_argument('--skip-dmas', dest='skipdmas', action='store_true',
#                     help='Skip files which are only on DMAS')

args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )

## If given, load JSON, otherwise initialize an empty config struct

# config = {}
#
# if args.config:
#     if Path(args.config).exist:
#         with open(args.config) as fp:
#             logging.info("Loading configuration from %s" % args.config)
#             config = json.load(args.config)
#
#     elif args.config == '-':
#         config = json.load(sys.stdin)


# if args.basename:
#     config["selector"] = { "basename": { "$in": args.basename } }
#
# if args.job:
#     config["job_id"] = args.job
#
#
# if not config["selector"]:
#     logging.error("No basenames provided")
#     exit()
#
# ## Default
# config["dest"] = { "minio": { "host": "covis-nas",
#                             "bucket": "postprocessed" }}

# # Validate configuration
# if "dest" not in config:
#     logging.error("No destination provided")
#     exit()
#
# client = db.CovisDB(MongoClient(args.dbhost))
#
# prefix = ""
# if "job_id" in config:
#     prefix = "by_job_id/%s" % config["job_id"]
# else:
#     prefix = "no_job_id/%s" % datetime.now().strftime("%Y%m%d-%H%M%S")

## If specified, load the JSON configuration
for input in args.inputs:

# with client.runs.find(config["selector"]) as results:
#
#     for r in results:

    output = args.outputDir

    logging.info("Processing input: %s" % input)
    logging.info("       to output: %s" % output)

    if not args.dryrun:

        if args.runlocal:
            job = postprocess.do_postprocess( input, output,
                                    autoOutputPath = args.autoOutputPath )

        else:
            job = postprocess.do_postprocess.delay( input, output,
                                    autoOutputPath = args.autoOutputPath )


    else:
        print("Dry run, skipping...")
