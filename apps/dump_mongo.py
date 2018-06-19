#!/usr/bin/env python3

import json
from pprint import pprint
import argparse
import sys

from pymongo import MongoClient
from decouple import config
from covis_db import db


parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

args = parser.parse_args()

client = db.CovisDB( MongoClient(args.dbhost ) )
cursor = client.runs.find().sort('datetime')

for elem in cursor:
    pprint(elem)

print("%d elements in total" % cursor.count(), file=sys.stderr)
