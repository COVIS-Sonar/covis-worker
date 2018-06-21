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

parser.add_argument('--fix', action='store_true')

parser.add_argument('hosts', nargs='+',
                    help='')

args = parser.parse_args()

client = db.CovisDB(MongoClient(args.dbhost))


for host in args.hosts:

    host = host.upper()

    ## Should DRY this
    raw = db.CovisRaw({"host":host, "filename":""})
    accessor = raw.accessor()

    mio = accessor.minio_client()

    objects = mio.list_objects( accessor.bucket, recursive=True )

    for obj in objects:
        # print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
        #         obj.etag, obj.size, obj.content_type)

        filename = str(obj.object_name)
        basename = misc.make_basename(filename)

        print("Checking database for basename %s" % basename)
        run = client.find(basename)

        if run:
            print("   Basename %s exists in database" % basename)

            raw = run.find_raw( host, filename )
            if raw:
                print(" ... and has raw for host %s" % host)
            else:
                print(" ... but does not have raw entry for host %s." % host)

                if args.fix:
                    print("FIX:   Adding raw entry for %s to database" % host)
                    run.add_raw(host,filename)

        else:
            print("!!! Basename %s is not in database" % basename)

            if args.fix:
                print("FIX: Adding run for %s" % basename)
                run = client.add_run(basename)

                if not run:
                    print("FIX:   Error adding run for basename %s" % basename)
                    continue

                run.add_raw(host,filename)
