#!/usr/bin/env python3

import json
from pprint import pprint
import sys

from pymongo import MongoClient

parser = argparse.ArgumentParser()

parser.add_argument('--log', metavar='log', nargs='?', default='WARNING',
                    help='Logging level')

parser.add_argument('--dbhost', default='localhost', help='Hostname of MongoDB host')

args = parser.parse_args()

client = MongoClient(args.dbhost)
db = client.covis
runs = db.runs
cursor = runs.find().sort('datetime')

for elem in cursor:
    pprint(elem)

print("%d elements in total" % cursor.count(), file=sys.stderr)
