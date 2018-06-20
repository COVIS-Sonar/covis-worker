from __future__ import absolute_import, unicode_literals
from .celery import app

import tempfile
import pathlib
import logging
import os
from subprocess import Popen,PIPE
import gzip
import shutil
import tarfile

import hashlib as hash

from covis_db import hosts,db

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

    print("Using source file %s:%s" % (raw.host, raw.filename))

    workdir = tempfile.TemporaryDirectory(dir=tempdir).name


    # Calculate output filename
    # TODO make more flexible to different dest_fmts
    outfile = pathlib.Path(workdir, basename+".tar.7z")

    accessor = raw.accessor()
    # accessor.hostname = "localhost"

    if not accessor:
        print("Unable to get file %s" % basename)
        return False

    r = accessor.reader()
    logging.info(r.info())

    # Remove existing destination file
    if os.path.isfile(outfile):
        logging.warning("Removing existing file")
        os.remove(outfile)


    do_update_contents = True

    if do_update_contents:
        decompressed_path = "/tmp"

        with tarfile.open(fileobj=r,mode="r:*") as tf:
            tf.extractall(path=decompressed_path)
            mem = tf.members

            contents = [tarInfoToContentsEntry(ti, decompressed_path) for ti in mem]

            print(contents)

        return True
    else:
        # If not updating contents, this can be done as a stream operation
        command = ["7z", "a", "-si", "-y", outfile]
        with Popen(command, stdin=PIPE) as process:
            with gzip.GzipFile(fileobj=r) as data:
                shutil.copyfileobj(data, process.stdin)


    # Check the results
    command = ["7z", "t", outfile]
    child = Popen(command)
    child.wait()

    if child.returncode != 0:
        logging.error("7z test on file %s has non-zero return value" % outfile)
        return False

    logging.info("Uploading to destination host %s" % dest_host)

    logging.info("Updating DB")
    raw = {'host': dest_host, 'path': raw.filename}
    print(raw)



def tarInfoToContentsEntry(ti, workdir):
    ## Calculated
    sha = shasum(pathlib.Path(workdir, ti.name))

    return {'name': ti.name,
            'size': ti.size,
            'sha1': sha}


def shasum(path):
    # Specify how many bytes of the file you want to open at a time
    BLOCKSIZE = 65536

    sha = hash.sha1()
    with open(path, 'rb') as infile:
        file_buffer = infile.read(BLOCKSIZE)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = infile.read(BLOCKSIZE)

    return sha.hexdigest()
