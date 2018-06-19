#!/usr/bin/env python3

import json
import argparse
import re
import logging
from datetime import datetime

from decouple import config

from pymongo import MongoClient
import os.path

import csv

from covis_db import db

from itertools import islice


parser = argparse.ArgumentParser()
parser.add_argument('infile', nargs=1,
                    help="JSON file to be processed",
                    type=argparse.FileType('r'))

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='INFO'),
                    help='Logging level')

parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

group = parser.add_mutually_exclusive_group()
group.add_argument('--dmas', dest="dmas", action='store_true')
group.add_argument('--covis-nas', nargs=1 )

args = parser.parse_args()

logging.basicConfig( level=args.log.upper() )


files = []

if args.dmas:

    # The DMAS data is just a list of filenames in JSON
    for filename in json.load(args.infile[0]):

        ## Strip off extension
        elem = os.path.splitext(filename)

        if elem[1] != '.tar':
            continue

        files.append( { 'basename': elem[0],
                        'file_entry': { 'host': "DMAS",
                                'filename': filename }})

elif args.covis_nas:
    # logging.info("Handling covis-nas data")
    #
    for row in args.infile[0].readlines():
        row = row.split()

        if( len(row) != 3 ):
            continue

        filename = re.sub("^\.\/", "", row[2])

        ## Need to extract basename
        basename = re.sub( "\.[\.\w]*\Z", "", os.path.basename(filename) )

        files.append( { 'basename': basename,
                        'file_entry': { 'host': args.covis_nas[0].upper(),
                                'filename': filename }} )

else:

    logging.error("Pleae use either --dmas or --covis-nas")

client = db.CovisDB( MongoClient(args.dbhost ) )
client.runs.create_index( "basename", unique=True)

## Take the input file and create a dict of { basename : {file_entry}}

for entry in files:

    ## Break filename apart
    basename = entry['basename']
    parts = re.split(r'[\_\-]', basename)

    date = datetime.strptime(parts[1], "%Y%m%dT%H%M%S.%fZ")
    mode = parts[2]

    # Insert validation here
    file_entry = entry['file_entry']

    entry = { 'datetime': date,
            'mode': mode,
            'site': 'Endeavour' }


    try:
        # This seems awkward, make a complete entry
        new_entry = {'basename': basename,
                     'raw': [file_entry]}
        new_entry.update(entry)

        client.runs.insert_one( new_entry )
        logging.info("Adding entry to db for %s" % basename)

    except pymongo.errors.DuplicateKeyError as err:
        logging.info("Updating existing entry for %s" % basename)

        res = client.runs.update_one(
            {'basename': basename},
            { '$set': entry,
              '$pull': { "raw": { "host": file_entry['host'] } } } )
        client.runs.update_one(
            {'basename': basename},
            { '$push': { "raw": file_entry } } )
