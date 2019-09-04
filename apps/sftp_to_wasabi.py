#!/usr/bin/env python3

# from pprint import pprint
import argparse
# import sys
# import json
import logging
import shutil
import stat
import os
import re

import boto3
from botocore.exceptions import ClientError

from pymongo import MongoClient
# from bson import json_util
from decouple import config
from covis_db import db, hosts, misc
from datetime import datetime

from paramiko.client import SSHClient,AutoAddPolicy
from urllib.parse import urlparse
import getpass

#from covis_worker import process

parser = argparse.ArgumentParser()

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='DEBUG'),
                    help='Logging level')

parser.add_argument('--quiet', action='store_true')
parser.add_argument('--force', dest='force', action='store_true')

parser.add_argument('--dry-run', dest='dryrun', action='store_true')

parser.add_argument('--privkey',
                    default=config('SFTP_PRIVKEY', default=None),
                    nargs='?')

parser.add_argument('--bucket',
                    default=config('S3_BUCKET', default=None),
                    nargs='?')

parser.add_argument('--privkey-password', dest="privkeypassword",
                    default=config('SFTP_PRIVKEY_PASSWORD', default=""),
                    nargs='?')

parser.add_argument('--regex',
                    default=config('FILTER_REGEX', default=""),
                    nargs='?')

parser.add_argument('sftpurl', action='store')

# parser.add_argument('--skip-dmas', dest='skipdmas', action='store_true',
#                     help='Skip files which are only on DMAS')

args = parser.parse_args()
logging.basicConfig( level=args.log.upper() )

if not args.bucket:
    logging.error("Must provide bucket or set S3_BUCKET")
    exit()

pattern = re.compile(args.regex)

## Open db client
srcurl = urlparse(args.sftpurl)
username = srcurl.username if srcurl.username else getpass.getuser()
port = srcurl.port if srcurl.port else 22

if not args.privkey:
    logging.error("Need to specify private key with SFTP_PRIVKEY or --privkey options")
    exit()

if not os.path.exists( args.privkey ):
    logging.error("Private key file %s does not exist"  % args.privkey )
    exit()

logging.info("Connecting to %s:%d as %s with privkey %s" % (srcurl.hostname, port, username,args.privkey))

client = SSHClient()
client.set_missing_host_key_policy(AutoAddPolicy)  ## Ignore host key for now...
client.connect(srcurl.hostname,
                username=username,
                key_filename=args.privkey,
                passphrase=args.privkeypassword,
                port=port,
                allow_agent=True)

sftp = client.open_sftp()
logging.info("Changing to path %s" % srcurl.path)
sftp.chdir(srcurl.path)

## Meanwhile, setup the S3 connection as well

s3 = boto3.resource('s3',
                    endpoint_url = 'https://s3.us-east-1.wasabisys.com',
                    aws_access_key_id = config("S3_ACCESS_KEY"),
                    aws_secret_access_key = config("S3_SECRET_KEY"))

bucket = s3.Bucket(args.bucket)

out_msgs = []

def sftp_walk(remotepath):
    path=remotepath
    files=[]
    folders=[]
    for f in sftp.listdir_attr(remotepath):
        if stat.S_ISDIR(f.st_mode):
            folders.append(f.filename)
        else:
            files.append(f.filename)

    if files:
        yield path, files

    for folder in folders:
        newpath = os.path.join(remotepath,folder)
        for x in sftp_walk(newpath):
            yield x

for path,files in sftp_walk(""):

    for file in files:

        if not pattern.match(file):
            logging.debug("Skipping %s" % file)
            continue

        logging.info("Considering remote file %s" % file)

        if args.bucket == "covis-raw":
            if not misc.is_covis_file(file):
                logging.info("   ... not a COVIS raw file, skipping...")
                continue

            filename,ext = misc.splitext(file)
            s3_file = misc.make_pathname( file, suffix=ext )

        else:
            s3_file = os.path.join(path,file)

        sftp_fullpath = os.path.join(srcurl.path,path,file)

        logging.info("S3 filename: %s" % s3_file )

        try:
            obj = s3.Object(args.bucket, str(s3_file))
            s3_obj = obj.load()
        except ClientError as e:
            if int(e.response['Error']['Code']) == 404:
                ## Object does not exist
                pass
            else:
                ## Some other error
                raise
        else:
            logging.debug("The object %s exists in the S3 bucket" % s3_file)

            ## Compare sizes
            sftp_stat = sftp.lstat( sftp_fullpath )

            sftp_size = sftp_stat.st_size
            s3_size  = obj.content_length;


            if sftp_size != s3_size:
                logging.info("Size mismatch (s3: %d bytes, sftp: %d bytes), attempting to re-download" % (s3_size, sftp_size))
            else:
                if not args.force:
                    continue
                else:
                    logging.info("   ... but --force specified, so doing it anyway")




        logging.info("Uploading file %s" % s3_file )

        if args.dryrun:
            logging.info(" .... dry run, skipping")
            continue

        #     ## Attempt to add to dest
        #
        #     logging.info("Uploading to destination host %s" % args.desthost)
        #
        #     run = db.make_run(basename=basename)
        #     raw = run.add_raw(args.desthost, make_filename=True)
        #     accessor = raw.accessor()
        #
        #     if not accessor:
        #         logging.error("Unable to get accessor for %s" % args.desthost)

        logging.info("Getting from SFTP: %s" % sftp_fullpath)

        with sftp.open(sftp_fullpath) as sftpfile:

            statinfo = sftpfile.stat()

            logging.info("Writing %d bytes to S3 as \"%s\"" % (statinfo.st_size,s3_file))
            bucket.upload_fileobj(sftpfile, s3_file)

        out_msgs.append("Uploaded %s" % s3_file)
        if not args.quiet:
          print("Uploaded %s" % s3_file)

client.close()

if len(out_msgs) > 0:
    ## Report results

    subject = "sftp_to_wasabi %s" % datetime.now().strftime("%c")


    sg_key = config("SENDGRID_API_KEY",None)
    if sg_key:
        import sendgrid
        from sendgrid.helpers.mail import *

        sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
        from_email = Email("amarburg@uw.edu")
        to_email = Email("amarburg@uw.edu")
        content = Content("text/plain", "\n".join(out_msgs))
        mail = Mail(from_email, subject, to_email, content )
        response = sg.client.mail.send.post(request_body=mail.get())

    mg_key = config("MAILGUN_API_KEY",None)
    if mg_key:
        import requests

        domain = "sandboxc489483675804e3dbbc362207206219c.mailgun.org"

        response = requests.post(
            "https://api.mailgun.net/v3/%s/messages" % domain,
            auth=("api", mg_key),
            data={"from": "amarburg@uw.edu",
                  "to": ["amarburg@uw.edu"],
                  "subject": subject,
                  "text": "\n".join(out_msgs)})

        logging.debug(response)
