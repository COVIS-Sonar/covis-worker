#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json
import pathlib
import logging

from pymongo import MongoClient
from decouple import config
from covis_db import db,hosts,remote,misc

from minio.error import ResponseError, NoSuchKey

from minio_validators.validation_main import do_validate


parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

parser.add_argument('--dry-run', action='store_true')

parser.add_argument('--fix', action='store_true',
                    help="Attempt to automatically fix any errors (by default, script does not attempt to fix)")

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='INFO'),
                    help='Logging level')

parser.add_argument('--hosts', nargs='*', default=["covis-nas"],
                    help='Minio hostname...')

parser.add_argument('filenames', nargs='*',
                    help='Basenames to check')


args = parser.parse_args()

client = db.CovisDB(MongoClient(args.dbhost))
logging.basicConfig( level=args.log.upper() )


for host in args.hosts:

    host = host.upper()

    if not hosts.validate_host(host):
        logging.warning("Host \"%s\" is not a valid covis host" % host)
        continue

    ## Should DRY this
    raw = db.CovisRaw({"host":host, "filename":""})
    accessor = raw.accessor()

    if not accessor:
        logging.warning("Unable to create accessor to %s" % host)
        continue

    mio = accessor.minio_client()

    if len(args.filenames) > 0:

        for filename in args.filenames:
            do_validate(args, host, client, mio, filename)


    else:

        objects = mio.list_objects( accessor.bucket, recursive=True )

        for obj in objects:
            # print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
            #         obj.etag, obj.size, obj.content_type)

            filename = str(obj.object_name)

            do_validate(args, host, client, mio, filename)
