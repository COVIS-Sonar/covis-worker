#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json

from pymongo import MongoClient
from bson import json_util
from decouple import config
from covis_db import db


parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

parser.add_argument('--dest-host', default="COVIS-NAS",
                    help='Destination host')

parser.add_argument('--dry-run', dest='dryrun', action='store_true')



args = parser.parse_args()

client = db.CovisDB(MongoClient(args.dbhost))

# Find run which are _not_ on NAS
result = client.runs.aggregate( [
    {"$match": { "raw.host": { "$not": { "$eq": "COVIS-NAS" } } } }
])

for elem in result:

    locations = [raw['host'] for raw in elem['raw']]

    print("Basename %s is on %s" % (elem['basename'], ','.join(locations)))


    if not args.dryrun:



    else:
        print("Dry run...")
