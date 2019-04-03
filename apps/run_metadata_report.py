#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json
import pathlib
import logging
import csv
import datetime

from pymongo import MongoClient
from decouple import config
from os import path

from covis_db import db,hosts,remote,misc

parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='INFO'),
                    help='Logging level')

parser.add_argument('--output', default=None)

## Limit of 0 means "no limit" to the MongoDB limit() function
parser.add_argument('--count', type=int, default=0, help='')

parser.add_argument("--sites", nargs='*', default=['Ashes','Endeavour'])


args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )
sites = [s.lower() for s in args.sites]


if args.output:
    outfile = open(args.output,'w', newline='')
else:
    outfile = sys.stdout

writer = csv.writer(outfile)


client = db.CovisDB(MongoClient(args.dbhost))

outfile.write("# %s\n" % ','.join(['basename','datetime',\
                'site','mode','raw_size','gz_size','7z_size']) )

for run in client.runs.find({}, limit=args.count ):

    run = db.CovisRun(run, collection=client.runs)

    if ('ashes' in sites and run.datetime > datetime.datetime(2018,7,1)) or \
       ('endeavour' in sites and run.datetime < datetime.datetime(2018,1,1)):

        logging.debug("Checking basename %s" % run.basename)

        ## Set these to None so the CSV field is empty if these values can't be determined
        raw_size = None
        nas_size = None
        gz_size = None

        if 'contents' in run.json:
            for file in run.json['contents']:
                if 'size' in file:
                    if not raw_size:
                        raw_size = 0

                    raw_size = raw_size + file['size']

        for raw in run.raw:
            if hosts.is_nas(raw.host):
                nas_size = raw.filesize
            elif hosts.is_wasabi(raw.host):
                gz_size = raw.filesize

        row = [run.basename, run.datetime.isoformat(),  \
                run.site, run.mode,
                raw_size, gz_size, nas_size ]

        writer.writerow(row)
