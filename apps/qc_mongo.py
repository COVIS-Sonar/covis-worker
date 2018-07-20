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
dmas_count = runs.find({'site': 'ONC', 'raw.host': 'DMAS'}).count()
print("% 6d are located at ONC, and have entries at DMAS" % dmas_count )


## I'm sure this is a terrible, terrible thing
nas_count = runs.find({'site': 'ONC', "$or": [{'raw.host': 'COVIS-NAS1'},
                                              {'raw.host': 'COVIS-NAS2'},
                                              {'raw.host': 'COVIS-NAS3'},
                                              {'raw.host': 'COVIS-NAS4'},
                                              {'raw.host': 'COVIS-NAS5'},
                                              {'raw.host': 'COVIS-NAS6'}]}).count()
print("% 6d are located on at least one NAS" % nas_count)

print("% 6d ONC files exist somewhere but not at DMAS" % (onc_count - dmas_count))
