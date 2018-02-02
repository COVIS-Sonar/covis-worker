#!/usr/bin/env python3

import json
import argparse
import re
import logging
from datetime import datetime

import pymongo
from pymongo import MongoClient
import os.path



parser = argparse.ArgumentParser()
parser.add_argument('infile', nargs=1,
                    help="JSON file to be processed",
                    type=argparse.FileType('r'))

parser.add_argument('--log', metavar='log', nargs='?', default='WARNING',
                    help='Logging level')

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )

# Loading a JSON object returns a dict.
j = json.load(args.infile[0])

client = MongoClient()
db = client.covis
runs = db.runs


runs.create_index( "name", unique=True )

for filename in j:

    if not filename.lower().endswith(".tar"):
        continue

    ## Strip off extension
    elem = os.path.splitext(filename)[0]

    ## Break filename apart
    parts = re.split(r'[\_\-]', elem)

    basename = elem
    date = datetime.strptime(parts[1], "%Y%m%dT%H%M%S.%fZ")
    mode = parts[2]

    # Insert validation here
    file_entry = { 'host': 'DMAS',
            'compression': "gz" }

    entry = { 'filename': filename,
            'datetime': date,
            'mode': mode,
            'site': 'ONC' }


    try:
        # This seems awkward, make a complete entry
        new_entry = {'name': basename,
                     'files': [file_entry]}
        new_entry.update(entry)

        runs.insert_one( new_entry )
        logging.info("Added entry to db for %s" % basename)

    except pymongo.errors.DuplicateKeyError as err:
        logging.info("Updating existing entry for %s" % basename)

        res = runs.update_one(
            {'name': basename},
            { '$set': entry,
              '$pull': { "files": { "host": "dmas" } } } )
        runs.update_one(
            {'name': basename},
            { '$push': { "files": file_entry } } )
