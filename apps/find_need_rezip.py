#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json

from pymongo import MongoClient
from bson import json_util
from decouple import config
from covis_db import db, hosts

from covis_worker import rezip,sample_tasks


parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', default=config('MONGODB_URL',
                    default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

parser.add_argument('--dest-host', dest="desthost", default="COVIS-NAS",
                    help='Destination host')

parser.add_argument('--count', default=0, type=int,
                        metavar='N',
                        help="Only queue N entries (used for debugging)")

parser.add_argument('--dry-run', dest='dryrun', action='store_true')

args = parser.parse_args()

# Validate destination hostname
if not hosts.validate_host(args.desthost):
    print("Can't understand destination host \"%s\"" % args.desthost)
    exit()

client = db.CovisDB(MongoClient(args.dbhost))

# Find run which are _not_ on NAS
result = client.runs.aggregate( [
    {"$match": { "$and":
                [ { "raw.host": { "$not": { "$eq": "COVIS-NAS" } } },
                  { "mode":     {"$eq": "DIFFUSE"}} ]
    } }
])

i = 0
for elem in result:
    run = db.CovisRun(elem)

    ## Skip DMAS entries for now
    raw = hosts.best_raw(run.raw)
    if hosts.is_dmas(raw.host):
        print("Skipping entry that's only on DMAS for now...")
        continue

    i = i+1
    if args.count > 0 and i > args.count:
        break




    locations = [raw.host for raw in run.raw]

    print("Basename %s is on %s" % (run.basename, ','.join(locations)))


    if not args.dryrun:
        job = rezip.rezip.delay(run.basename,args.desthost)


    else:
        print("Dry run...")
