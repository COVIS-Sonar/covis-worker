#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json
import pathlib
import re
import datetime

from pymongo import MongoClient
from decouple import config
from covis_db import db,hosts,misc

import pandas as pd

parser = argparse.ArgumentParser()

# parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
#                     help='URL (mongodb://hostname/) of MongoDB host')
# parser.add_argument('--dry-run', action='store_true')
#
# parser.add_argument('--fix', action='store_true')
#
# parser.add_argument('hosts', nargs='+',
#                     help='')



args = parser.parse_args()

# client = db.CovisDB(MongoClient(args.dbhost))

host = "COVIS-NAS"

## Should DRY this
raw = db.CovisRaw({"host":host, "filename":""})
accessor = raw.accessor()
mio = accessor.minio_client()
objects = mio.list_objects( accessor.bucket, recursive=True )

entries = []

for obj in objects:
    # print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
    #         obj.etag, obj.size, obj.content_type)

    filename = str(obj.object_name)
    basename = misc.make_basename(filename)

    ## Break filename apart
    parts = re.split(r'[\_\-]', basename)

    if len(parts) != 3:
        continue

    try:
        date = datetime.datetime.strptime(parts[1], "%Y%m%dT%H%M%S.%fZ")
    except ValueError:

        try:
            date = datetime.datetime.strptime(parts[1], "%Y%m%dT%H%M%S")
        except ValueError:
            continue

    mode = parts[2]

    # Insert validation here
    entries.append( { 'basename': basename,
            'sonar_date': date,
            'sonar_mode': mode } )

    # if len(entries) > 1000:
    #     break;

## Put all of the data in a Pandas dataframe
df = pd.DataFrame( entries )
# print(df)

## Select only the diffuse entries
diffuse = df[ df.sonar_mode.str.match(r'.*diffuse.*', case=False) ]

## Group by day (from https://stackoverflow.com/questions/48961892/python-pandas-group-by-day-and-count-for-each-day)
grouped = diffuse['sonar_mode'].groupby(by=diffuse['sonar_date'].dt.date).count()
grouped = grouped.reindex(pd.to_datetime(grouped.index))
# print(grouped)

current_year = grouped[(grouped.index.year== 2018) | (grouped.index.year== 2019)]
# print(current_year)

print(current_year.to_csv())






    #
    # print("Checking database for basename %s" % basename)
    # run = client.find(basename)
    #
    # if run:
    #     print("   Basename %s exists in database" % basename)
    #
    #     raw = run.find_raw( host, filename )
    #     if raw:
    #         print("    and has raw for host %s" % host)
    #     else:
    #         print("!!! but does not have raw entry for host %s." % host)
    #
    #         if args.fix:
    #             print("FIX:   Adding raw entry for %s to database" % host)
    #             run.add_raw(host,filename)
    #
    # else:
    #     print("!!! Basename %s is not in database" % basename)
    #
    #     if args.fix:
    #         print("FIX: Adding run for %s" % basename)
    #         run = client.add_run(basename)
    #
    #         if not run:
    #             print("FIX:   Error adding run for basename %s" % basename)
    #             continue
    #
    #         run.add_raw(host,filename)
