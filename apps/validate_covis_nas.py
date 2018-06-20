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

parser.add_argument('--dry-run', action='store_true')

args = parser.parse_args()

client = db.CovisDB(MongoClient(args.dbhost))



result = client.runs.aggregate( [
    {"$match": { "raw.host": { "$not": { "$eq": "COVIS-NAS" } } } }
])


for elem in result:
    pprint(elem)

#print("%d elements in total" % cursor.count(), file=sys.stderr)
