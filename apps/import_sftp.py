#!/usr/bin/env python3

# from pprint import pprint
import argparse
# import sys
# import json
import logging
import shutil
import re

from pymongo import MongoClient
# from bson import json_util
from decouple import config
from covis_db import db, hosts, misc
from covis_worker import rezip

from paramiko.client import SSHClient,AutoAddPolicy
from urllib.parse import urlparse
import getpass

#from covis_worker import process

parser = argparse.ArgumentParser()

# parser.add_argument('--config', default=config('PROCESS_CONFIG',""),
#                     help="Process.json files.  Can be a path, URL, or '-' for stdin")

parser.add_argument('--dbhost', default=config('MONGODB_URL',
                    default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

parser.add_argument('--dest-host', dest="desthost", default="COVIS-NAS",
                    help='Destination host')

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='INFO'),
                    help='Logging level')
#
# parser.add_argument('--job', metavar='log', nargs='?',
#                     help='Job name')
#
# parser.add_argument('--count', default=0, type=int,
#                     metavar='N',
#                     help="Only queue N entries (used for debugging)")

parser.add_argument('--force', dest='force', action='store_true')

parser.add_argument('--dry-run', dest='dryrun', action='store_true')

parser.add_argument("--run-local", dest='runlocal', action='store_true')

parser.add_argument('--privkey', default=config("SFTP_PRIVKEY",default=""), nargs='?')

parser.add_argument('--regex',
                    default=config('FILTER_REGEX', default=""),
                    nargs='?')

parser.add_argument('--postprocess',
                    default=False,
                    action="store_true")

parser.add_argument('sftpurl', action='store')

# parser.add_argument('--skip-dmas', dest='skipdmas', action='store_true',
#                     help='Skip files which are only on DMAS')

args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )

#-- Validate inputs
if not args.privkey:
    logging.error("Need to specify private key with SFTP_PRIVKEY or --privkey options")
    exit()

pattern = re.compile(args.regex)


## Open db client
db = db.CovisDB(MongoClient(args.dbhost))

srcurl = urlparse(args.sftpurl)
print(srcurl)
username = srcurl.username if srcurl.username else getpass.getuser()
port = srcurl.port if srcurl.port else 22

logging.info("Connecting to %s:%d as %s" % (srcurl.hostname, port, username))

client = SSHClient()
client.set_missing_host_key_policy(AutoAddPolicy)  ## Ignore host key for now...
client.connect(srcurl.hostname,
                username=username,
                key_filename=args.privkey,
                passphrase=config("PRIVKEY_PASSPHRASE",""),
                port=port,
                allow_agent=True)

sftp = client.open_sftp()

logging.info("Changing to path %s" % srcurl.path)
sftp.chdir(srcurl.path)

for remote_file in sftp.listdir():

    if not pattern.search(remote_file):
        logging.debug("Skipping %s" % remote_file)
        continue

    logging.info("Considering remote file %s" % remote_file)

    if not misc.is_covis_file(remote_file):
        logging.info("   ... not a COVIS raw file, skipping...")
        continue

    basename = misc.make_basename(remote_file)
    run = db.find(basename)

    if run and not args.force:
        logging.info("Basename %s already exists" % basename)

        ## Todo.  Handle

    else:
        logging.info("Basename %s does not exist, uploading to %s" % (basename, args.desthost))

        if args.dryrun:
            logging.info(" .... dry run, skipping")
            continue

        if args.runlocal:
            run = rezip.rezip_from_sftp(srcurl.geturl() + "/" + remote_file, args.desthost,
                                        privkey=args.privkey)


            if args.postprocess:
                logging.info(" .... automatically postprocessing")

        else:
            job = rezip.rezip.rezip_from_sftp.delay(srcurl.geturl() + "/" + remote_file,args.desthost,
                                        privkey=args.privkey)

        ## Attempt to add to dest
        #
        # logging.info("Uploading to destination host %s" % args.desthost)
        #
        # run = db.make_run(basename=basename)
        # raw = run.add_raw(args.desthost, make_filename=True)
        # accessor = raw.accessor()
        #
        # if not accessor:
        #     logging.error("Unable to get accessor for %s" % args.desthost)
        #
        # with sftp.open(remote_file) as sftpfile:
        #
        #     statinfo = sftpfile.stat()
        #
        #     print("Writing %d bytes to %s:%s" % (statinfo.st_size,raw.host,raw.filename))
        #     accessor.write(sftpfile, statinfo.st_size)
        #
        #
        # logging.info("Upload successful, updating DB")
        #
        # run = db.insert_run(run)
        # if not run:
        #     logging.info("Error inserting into db...")
        #
        # ## Ugliness
        # run.insert_raw(raw)
