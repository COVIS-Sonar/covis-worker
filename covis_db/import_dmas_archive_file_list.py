#!/usr/bin/env python3

import json
import argparse
import re
from datetime import datetime

from pymongo import MongoClient
import os.path

parser = argparse.ArgumentParser()
parser.add_argument('infile', nargs=1,
                    help="JSON file to be processed",
                    type=argparse.FileType('r'))
arguments = parser.parse_args()

# Loading a JSON object returns a dict.
j = json.load(arguments.infile[0])


db_elements = []

for elem in j:

    if not elem.lower().endswith(".tar"):
        continue

    ## Strip off extension
    elem = os.path.splitext(elem)[0]

    ## Break filename apart
    parts = re.split(r'[\_\-]', elem)

    print(parts)

    date = datetime.strptime(parts[1], "%Y%m%dT%H%M%S.%fZ")
    mode = parts[2]

    # Insert validation here

    db_elements.append( {'name': elem,
                         'datetime': date,
                        'type': mode,
                        'site': 'ONC'})

## Insert into db

print(db_elements)

client = MongoClient()
db = client.covis
db.runs.insert_many(db_elements)
