#!/usr/bin/env python3

# A thin Python wrapper around "mongodump" which takes the same
# configuration info as everything else

import argparse
from datetime import datetime
import subprocess
from os import path
import pathlib

from decouple import config

parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

parser.add_argument('output', default='dump', nargs=1)

parser.add_argument('--timestamp', action='store_true')


args = parser.parse_args()

dest = pathlib.Path(args.output[0])

if args.timestamp:
    ## Assume dest is a directory
    if not path.exists(dest):
        print('With --timestamp option, the dest should be an existing directory')
        exit()

    dest = dest / datetime.now().strftime("%d%m%Y_%H%M%S.bson.gz")

command = ['mongodump', '--uri=%s' % args.dbhost, '--gzip', '--archive=%s' % dest]
print(command)

subprocess.run(command)
