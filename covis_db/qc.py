#!/usr/bin/env python3

import json
from pprint import pprint
import sys

from pymongo import MongoClient

client = MongoClient()
db = client.covis
runs = db.runs

cursor = runs.find()

total_count = cursor.count()
print("% 6d total entries" % total_count)

onc_count = runs.find({'site': 'ONC'}).count()
print("% 6d are located at ONC" % onc_count )

## Find runs without a DMAS entry
cursor = runs.find({'site': 'ONC', 'raw.host': 'DMAS'})
dmas_count = cursor.count()
print("% 6d are located at ONC, and have entries at DMAS" % dmas_count )

print("% 6d ONC files exist somewhere but not at DMAS" % (onc_count - dmas_count))
