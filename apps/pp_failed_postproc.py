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

parser.add_argument('--output', nargs='?', default=None,
                    help='Filename for output (stdout if not specified)')

parser.add_argument('filename', nargs='?',
                    help='JSON output from validate_postprocessed.py to check')

args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )

with open(args.filename) as fp:
    data = json.load(fp)

for key,data in data.items():

    path = Path(key)

    if not data["has_mat"]:
        print( path.name )
