#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json
import pathlib

from pymongo import MongoClient
from decouple import config
from covis_db import db,hosts,remote,misc

parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

parser.add_argument('--dry-run', action='store_true')

parser.add_argument('--no-check-raw', action='store_true')

parser.add_argument('--fix', action='store_true')

args = parser.parse_args()

client = db.CovisDB(MongoClient(args.dbhost))

for run in client.runs.find({}):
    run = db.CovisRun(run, collection=client.runs)

    print("Checking %s" % run.basename)

    if args.no_check_raw:
        continue

    for raw in run.raw:
        if not raw.accessor().exists():
            print("    Can't find raw file on host %s" % raw.host)

            if args.fix:
                print("FIX: Dropping from run")
                run.drop_raw(raw)
