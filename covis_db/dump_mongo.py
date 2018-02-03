#!/usr/bin/env python3

import json
from pprint import pprint
import sys

from pymongo import MongoClient

client = MongoClient()
db = client.covis
runs = db.runs
cursor = runs.find()

for elem in cursor:
    pprint(elem)

print("%d elements in total" % cursor.count(), file=sys.stderr)
