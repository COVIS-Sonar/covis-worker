#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json
import pathlib
import logging
import re
from pathlib import Path

from decouple import config
from covis_db import db,hosts,accessor,misc

parser = argparse.ArgumentParser()

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='INFO'),
                    help='Logging level')

parser.add_argument('--prefix', nargs='?', default=config('POSTPROC_PREFIX', default=None),
                    help='Prefix appended to output filename')

parser.add_argument('--output', nargs='?', default=None,
                    help='Filename for output (stdout if not specified)')

parser.add_argument("--bucket", nargs='?', default=config('POSTPROC_BUCKET', default="postprocessed"),
                    help='Bucket for postprocessed data')

parser.add_argument('filenames', nargs='*',
                    help='Basenames to check')

args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )

if args.prefix:
    prefix_re = re.compile(args.prefix)

# Environment variables NAS_URL, NAS_ACCESS_KEY and NAS_SECRET_KEY must be set.
host = "covis-nas"

if not hosts.validate_host(host):
    logging.error("Host \"%s\" is not a valid covis host" % host)
    exit()

## Should DRY this
accessor = accessor.MinioAccessor( bucket=args.bucket, path="", config_base=hosts.config_base(host))

if not accessor:
    logging.error("Unable to create accessor to %s" % host)
    exit()

mio = accessor.minio_client()
objects = mio.list_objects( accessor.bucket, recursive=True )


class PPEntry:
    def __init__(self):
        self.has_mat = False
        self.has_metadata = False
        self.has_output = False


    def to_dict( self ):
        return {"has_mat": self.has_mat,
                "has_metadata": self.has_metadata,
                "has_output": self.has_output }

pp_entries = {}

for obj in objects:

    name = obj.object_name

    if prefix_re and None==prefix_re.match( name ):
            continue

    print(obj.bucket_name, name, obj.last_modified,
          obj.etag, obj.size, obj.content_type)

    path = Path(name)

    key = str(path.parent)
    filename = path.name

    if not key in pp_entries:
        pp_entries[key] = PPEntry()

    if path.suffix == '.mat':
        pp_entries[key].has_mat = True
    elif filename == 'metadata.json':
        pp_entries[key].has_metadata = True
    elif filename == 'output.txt':
        pp_entries[key].has_output = True


def custom_serializer(o):
    if isinstance(o, PPEntry):
        return o.to_dict()


if args.output:
    with open( args.output, 'w' ) as fp:
        json.dump(pp_entries, fp=fp, indent=2, default=custom_serializer)
else:
    json.dump(pp_entries, fp=sys.stdout, indent=2, default=custom_serializer)
