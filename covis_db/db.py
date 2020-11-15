
from pymongo import MongoClient,ReturnDocument,errors
import re

import datetime
import logging

from decouple import config

import shutil
import subprocess
import glob
from pathlib import Path

from os import path
from . import accessor,hosts,misc


def retry(num_tries, exceptions):
    def decorator(func):
        def f_retry(*args, **kwargs):
            for i in range(num_tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logging.info("Exception, retrying...")
                    continue
        return f_retry
    return decorator

retry_auto_reconnect = retry(3, (errors.AutoReconnect,))



# Thin wrapper around MongoDB client accessor
#
class CovisDB:

    def __init__(self, db_client=None):

        if db_client:
            self.client = db_client
        else:
            mongo_url = config('MONGODB_URL', default="mongodb://localhost/")
            self.client = MongoClient(mongo_url)

        self.db = self.client[config('MONGODB_DB', default='covisprod')]
        self.runs = self.db[config('MONGODB_RUNS_TABLE', default='runs')]

    def find(self, basename):
        r = self.runs.find_one({'basename': basename})
        if r:
            return CovisRun(r,collection=self.runs)
        else:
            return None

    def find_regex(self, reg):
        results = self.runs.find( {'basename' : {"$regex" : reg}} )

        return [ CovisRun(r,collection=self.runs) for r in results ]

    def insert_run(self, run):
        self.runs.replace_one({'basename':run.basename}, run.json, upsert=True)
        return self.find(run.basename)

    def add_run(self, basename, update=False):
        existing = self.find(basename)

        if existing:
            if not update:
                logging.info("Basename %s exists, not adding" % basename)
                return None

            logging.info("Basename %s exists, forcing update" % basename)

        entry = self.make_run(basename)

        # Preserve entries from existing
        if existing:
            entry['raw'] = existing['raw']
            self.runs.remove({'basename': basename})

        self.runs.insert_one(entry)
        return self.find(basename)


    def make_run(self,basename):
        ## Break filename apart
        date,mode = misc.split_basename(basename)

        # Insert validation here
        entry = { 'basename': str(basename),
                'datetime': date,
                'mode': mode }

        if date < datetime.datetime(2016,1,1):
                entry['site'] = 'Endeavour'
        else:
                entry['site'] = 'Ashes'

        return CovisRun(entry)



class CovisRun:

    def __init__(self, json, collection=None):
        self.collection = collection
        self.json = json

    def toJSON(self):
        return self.json

    @property
    def basename(self):
        return self.json["basename"]

    @property
    def datetime(self):
        return self.json["datetime"]

    @property
    def mode(self):
        return self.json["mode"]

    @property
    def site(self):
        return self.json["site"]

    @property
    def raw(self):
        return [CovisRaw(p) for p in self.json["raw"]]

    # Check if it already exists
    def find_raw(self,host):
        #entry = {'host': host } #, 'filename': filename}
        #print("Searching for %s" % entry)

        host = host.upper()

        if self.collection:
            f = self.collection.find_one({'basename': self.basename,
                                            'raw.host': {'$eq': host } } )

            ## Find the matching element in the raw array
            if f:
                for r in f['raw']:
                    if r['host'] == host:
                        return CovisRaw(r)

        return False

    def insert_raw(self,raw):
        if self.collection:
            self.json = self.collection.find_one_and_update({'basename': self.basename},
                    {'$addToSet': {'raw': raw.json}},
                    return_document=ReturnDocument.AFTER)

    def add_raw(self,host,filename=None,filesize=None, make_filename=False,suffix='.7z'):

        host = host.upper()

        if not hosts.validate_host(host):
            logging.warning("Invalid host %s" % host)
            return False

        if make_filename:
            filename = Path(self.datetime.strftime("%Y/%m/%d/")) / self.basename
            filename = filename.with_suffix(suffix)

        raw = self.find_raw(host)
        if raw:
            logging.info("Raw already exists, not inserting")
            return raw

        entry = {'host': host, 'filename': str(filename)}
        if filesize:
            entry["filesize"] = filesize

        if self.collection:
            self.json = self.collection.find_one_and_update({'basename': self.basename},
                    {'$addToSet': {'raw': entry}},
                    return_document=ReturnDocument.AFTER)

        logging.info("Successfully added raw")

        return CovisRaw( entry )

    @retry_auto_reconnect
    def update_raw( self, entry ):
        if self.collection:
            self.collection.update({
                                'basename': self.basename,
                                'raw.host': entry["host"] },
                    { '$set' : {'raw.$': entry} })
            self.json = self.collection.find_one({'basename': self.basename})

        return CovisRaw(entry)

    @retry_auto_reconnect
    def update_contents( self, contents ):
        if self.collection:
            self.collection.find_one_and_update({'basename': self.basename},
                                                {'$set': {"contents": contents }})

    def drop_raw(self,raw):
        entry = {'host': raw.host, 'filename': raw.filename}

        if self.collection:
            print("Attempting to update collection")
            res = self.collection.find_one_and_update({'basename': self.basename},
                {'$pull': {'raw': entry}} )
            print(res)


class CovisRaw:

    def __init__(self, raw):
        self.json = raw

    def equal(self,host,filename):
        return self.host == host and self.filename == filename

    @property
    def host(self):
        return self.json['host'].upper()

    @property
    def filename(self):
        return self.json['filename']

    @property
    def filesize(self):
        if "filesize" in self.json:
            return self.json["filesize"]
        else:
            return None

    def accessor(self):
        if hosts.is_old_nas(self.host):
            return accessor.OldCovisNasAccessor(self)
        elif hosts.is_nas(self.host):
            return accessor.CovisNasAccessor(self)
        elif hosts.is_dmas(self.host):
            return accessor.DmasAccessor(path=self.filename)
        elif hosts.is_wasabi(self.host):
            return accessor.WasabiAccessor(path=self.filename)

    def reader(self):
        return self.accessor().reader()

    def stats(self):
        return self.accessor().stats()

    def extract(self, workdir):

        root,ext = path.splitext(self.filename)

        if ext == '.7z':
            command = ["7z", "e",  "-bd", "-y", "-o", workdir, "-si"]

            with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
                with self.reader() as data:
                    shutil.copyfileobj(data, process.stdin)

        elif ext == '.gz':
            command = ["tar", "-C", workdir, "-xzvf", "-"]

            with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
                with self.reader() as data:
                    shutil.copyfileobj(data, process.stdin)

        elif ext == '.tar':
            command = ["tar", "-C", workdir, "-xvf", "-"]

            with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
                with self.reader() as data:
                    shutil.copyfileobj(data, process.stdin)

        else:
            logging.error("Don't know how to handle extension: %s", ext)

        contents = glob.glob(workdir + "/APLUWCOVIS*/")

        return contents[0]
