from __future__ import absolute_import, unicode_literals
from .celery import app

import tempfile
from pathlib import Path
import logging
import os

import subprocess
import gzip
import shutil
import tarfile
from urllib.parse import urlparse
from decouple import config

import hashlib as hash

from paramiko.client import SSHClient,AutoAddPolicy

from covis_db import hosts,db,misc

@app.task
def rezip(basename, dest_host, dest_fmt='7z', src_host=[], tempdir=None):
    print("Rezipping %s and storing to %s" % (basename, dest_host))

    client = db.CovisDB()
    run = client.find(basename)

    if not run:
        # What's the canonical way to report errors
        logging.info("Couldn't find basename in db: %s", basename)
        return False

    raw = hosts.best_raw(run.raw)

    logging.info("Using source file %s:%s" % (raw.host, raw.filename))

    with tempfile.TemporaryDirectory(dir=tempdir) as workdir:

        # Calculate output filename
        # TODO make more flexible to different dest_fmts
        outfile = Path(workdir, basename+".7z")

        accessor = raw.accessor()
        # accessor.hostname = "localhost"

        if not accessor:
            print("Unable to get file %s" % basename)
            return False

        r = accessor.reader()

        # Remove existing destination file
        if os.path.isfile(str(outfile)):
            logging.warning("Removing existing file")
            os.remove(outfile)

        decompressed_path = workdir

        mode="r"

        ext = Path(raw.filename).suffix
        if ext == '.gz':
            mode="r:gz"

        contents = None

        ## Forces decode as gz file for now
        with tarfile.open(fileobj=r,mode=mode) as tf:
            tf.extractall(path=decompressed_path)
            mem = tf.getmembers()

            contents = [tarInfoToContentsEntry(ti, decompressed_path) for ti in mem if ti.isfile()]

            ## Recompress
            files = [str(n.name) for n in mem]

            #"-mx=9",
            command = ["7z", "a",  "-bd", "-y", str(outfile)] + files
            process = subprocess.run(command,cwd=str(decompressed_path))

            ## Update contents on run
            logging.info("Attempting to update contents in Mongodb...")
            run.update_contents( contents )

            # run.collection.find_one_and_update({'basename': run.basename},
            #                                     {'$set': {"contents": contents }})

        # else:
        #     # If not updating contents, this can be done as a streaming input-to-7z operation (w/o ever making a temporary file)
        #     with tarfile.open(fileobj=r,mode="r:gz") as tf:
        #         while True:
        #             mem = tf.next()
        #             if not mem:
        #                 break
        #
        #             command = ["7z", "a", "-bd", "-si%s" % mem.name, "-y", outfile]
        #
        #             with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
        #                 with tf.extractfile(mem) as data:
        #                     shutil.copyfileobj(data, process.stdin)


        # Check the results
        logging.info("Rezip complete, testing archive...")
        command = ["7z", "t", "-bd", str(outfile)]
        child = subprocess.Popen(command)
        child.wait()

        if child.returncode != 0:
            logging.error("7z test on file %s has non-zero return value" % str(outfile))
            return False

        dest_filename = misc.make_pathname( run.basename, date=run.datetime, suffix='.7z' )


        logging.info("Dest filename: %s" % str(dest_filename))

        logging.info("Uploading to destination host %s" % dest_host)
        raw = db.CovisRaw({'host': dest_host, 'filename': str(dest_filename)} )
        accessor = raw.accessor()

        if not accessor:
            logging.error("Unable to get accessor for %s" % dest_host)

        statinfo = os.stat(str(outfile))
        print("Writing %d bytes to %s:%s" % (statinfo.st_size,raw.host,raw.filename))
        with open(str(outfile), 'rb') as zfile:
            accessor.write(zfile,statinfo.st_size)

        logging.info("Upload successful, updating DB")
        if not run.add_raw(raw.host, filename=raw.filename, filesize=statinfo.st_size):
            logging.info("Error inserting into db...")



## Repeats above quite a lot.   Lots of potential for reducing the DRY...
@app.task
def rezip_from_sftp(sftp_url, dest_host, dest_fmt='7z', tempdir=None,
                    privkey=config("SFTP_PRIVKEY",""),
                    privkey_password=config("PRIVKEY_PASSPHRASE","")):
    print("Retrieving from SFTP site %s and storing to %s" % (sftp_url, dest_host))

    if not privkey:
        logging.error("Need to specify private key with SFTP_PRIVKEY or --privkey options")
        return

    dbclient = db.CovisDB()

    #sftp_url must be complete (with username and port)
    srcurl = urlparse(sftp_url)
    print(srcurl)

    srcpath = Path(srcurl.path)
    port = srcurl.port if srcurl.port else 22

    filename = srcpath.name
    basename = misc.make_basename(str(srcpath))

    logging.info("Connecting to %s:%d as %s" % (srcurl.hostname, port, srcurl.username))

    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy)  ## Ignore host key for now...
    client.connect(srcurl.hostname,
                    username=srcurl.username,
                    key_filename=privkey,
                    passphrase=privkey_password,
                    port=port,
                    allow_agent=True)

    sftp = client.open_sftp()

    with tempfile.TemporaryDirectory(dir=tempdir) as workdir:
        destfile = Path(workdir) / filename
        logging.info("Retrieving %s to temporary file %s" % (srcurl.path, destfile))

        sftp.get( srcurl.path, str(destfile) )

        # Calculate output filename
        # TODO make more flexible to different dest_fmts
        outfile = (Path(workdir) / basename).with_suffix(".7z")

        # Remove existing destination file
        if os.path.isfile(str(outfile)):
            logging.warning("Removing existing file")
            os.remove(outfile)

        decompressed_path = workdir
        mode="r"

        ext = destfile.suffix
        if ext == '.gz':
            mode="r:gz"

        ## Forces decode as gz file for now
        with tarfile.open(str(destfile),mode=mode) as tf:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tf, path=decompressed_path)
            mem = tf.getmembers()

            ## Generate metainfo about members
            contents = [tarInfoToContentsEntry(ti, decompressed_path) for ti in mem if ti.isfile()]

            ## Recompress
            files = [str(n.name) for n in mem]

            #"-mx=9",
            command = ["7z", "a",  "-bd", "-y", str(outfile)] + files
            process = subprocess.run(command,cwd=str(decompressed_path))

        logging.info(contents)

        ## Assume SFTP imports are new records
        # Check the results
        command = ["7z", "l", "-bd", str(outfile)]
        child = subprocess.Popen(command)
        child.wait()

        if child.returncode != 0:
            logging.error("7z test on file %s has non-zero return value" % str(outfile))
            return False

        statinfo = os.stat(str(outfile))

        run = dbclient.make_run(basename=basename)
        raw = run.add_raw(dest_host, make_filename=True, filesize=statinfo.st_size)
        if not raw or raw==False:
            logging.error("Unable to get raw for %s" % dest_host)
            exit()

        accessor = raw.accessor()

        # dest_filename = Path(run.datetime.strftime("%Y/%m/%d/")) / basename.with_suffix('.7z')
        # logging.info("Dest filename: %s" % str(dest_filename))
        # logging.info("Uploading to destination host %s" % dest_host)

        if not accessor:
            logging.error("Unable to get accessor for %s" % dest_host)

        print("Writing %d bytes to %s:%s" % (statinfo.st_size,raw.host,raw.filename))
        with open(str(outfile), 'rb') as zfile:
            accessor.write(zfile,statinfo.st_size)


        logging.info("Upload successful, updating DB")
        if(contents):
            run.json["contents"] = contents
        run = dbclient.insert_run(run)

        if not run:
            logging.info("Error inserting into db...")
        else:
            logging.debug("Successfully created run %s" % run.basename)

        ## Ugliness
        run.insert_raw(raw)

        logging.info("Completed rezip")

        return run.basename


def tarInfoToContentsEntry(ti, workdir):
    ## Calculated
    sha = shasum(Path(workdir, ti.name))

    return {'name': ti.name,
            'size': ti.size,
            'sha1': sha}


def shasum(path):
    # Specify how many bytes of the file you want to open at a time
    BLOCKSIZE = 65536

    sha = hash.sha1()
    with open(str(path), 'rb') as infile:
        file_buffer = infile.read(BLOCKSIZE)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = infile.read(BLOCKSIZE)

    return sha.hexdigest()
