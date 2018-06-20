from __future__ import absolute_import, unicode_literals
from .celery import app

import tempfile
import pathlib
import logging
import os

import subprocess
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

    workdir = "/tmp"  #tempfile.TemporaryDirectory(dir=tempdir).name


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
            mem = tf.getmembers()

            contents = [tarInfoToContentsEntry(ti, decompressed_path) for ti in mem]

            ## Recompress
            files = [n.name for n in mem]
            #"-mx=9",
            command = ["7z", "a",  "-y", outfile] + files
            process = subprocess.run(command,cwd=decompressed_path)

            run.collection.find_one_and_update({'basename': run.basename},
                                                {'$set': {"contents": contents }})

    else:
        # If not updating contents, this can be done as a streaming operation
        with tarfile.open(fileobj=r,mode="r:*") as tf:
            while True:
                mem = tf.next()
                if not mem:
                    break

                command = ["7z", "a", "-si%s" % mem.name, "-y", outfile]

                with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
                    with tf.extractfile(mem) as data:
                        shutil.copyfileobj(data, process.stdin)


    # Check the results
    command = ["7z", "t", outfile]
    child = subprocess.Popen(command)
    child.wait()

    if child.returncode != 0:
        logging.error("7z test on file %s has non-zero return value" % outfile)
        return False

    logging.info(raw.filename)
    dest_filename = pathlib.Path(raw.filename).parent / pathlib.Path(outfile).name
    logging.info("Dest filename: %s" % dest_filename)

    logging.info("Uploading to destination host %s" % dest_host)
    raw = db.CovisRaw({'host': dest_host, 'filename': str(dest_filename)} )
    accessor = raw.accessor()

    if not accessor:
        logging.error("Unable to get accessor for %s" % dest_host)

    statinfo = os.stat(outfile)
    print("Writing %d bytes to %s:%s" % (statinfo.st_size,raw.host,raw.filename))
    with open(outfile, 'rb') as zfile:
        accessor.write(zfile,statinfo.st_size)

    logging.info("Upload successful, updating DB")
    if not run.add_raw(raw.host, raw.filename):
        logging.info("Error inserting into db...")



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
