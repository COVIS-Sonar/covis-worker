
from pymongo import MongoClient,ReturnDocument
import re

import datetime

from decouple import config

from . import remote,hosts


# Thin wrapper around MongoDB client accessor
#
class CovisDB:

    def __init__(self, db_client=None):

        if db_client:
            self.client = db_client
        else:
            mongo_url = config('MONGODB_URL', default="mongodb://localhost/")
            print("Connecting to %s" % mongo_url)
            self.client = MongoClient(mongo_url)

        self.db = self.client[config('MONGODB_DB', default='covis')]
        self.runs = self.db[config('MONGODB_RUNS_TABLE', default='runs')]

    def find(self, basename):
        r = self.runs.find_one({'basename': basename})
        if r:
            return CovisRun(r,collection=self.runs)
        else:
            return None

    def add_run(self, basename, update=False):
        existing = self.find(basename)

        if existing:
            if not update:
                logging.info("Basename %s exists, not adding" % basename)
                return None

            logging.info("Basename %s exists, forcing update" % basename)

        ## Break filename apart
        parts = re.split(r'[\_\-]', basename)

        date = datetime.datetime.strptime(parts[1], "%Y%m%dT%H%M%S.%fZ")
        mode = parts[2]

        # Insert validation here
        entry = { 'basename': basename,
                'datetime': date,
                'mode': mode }

        if date < datetime.datetime(2016,1,1):
                entry['site'] = 'Endeavour'
        else:
                entry['site'] = 'Ashes'

        # Preserve entries from existing
        if existing:
            entry['raw'] = existing['raw']
            self.runs.remove({'basename': basename})

        self.runs.insert_one(entry)

        return self.find(basename)


class CovisRun:

    def __init__(self, json, collection=None):
        self.collection = collection
        self.json = json

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
    def raw(self):
        return [CovisRaw(p) for p in self.json["raw"]]

    # Check if it already exists
    def find_raw(self,host,filename):
        entry = {'host': host, 'filename': filename}
        f = self.collection.find_one({'basename': self.basename,
                'raw': {'$eq': entry } } )

        if f:
            return CovisRaw(f)
        return False

    def add_raw(self,host,filename):
        if not hosts.validate_host(host):
            return False

        if self.find_raw(host,filename):
            return False

        entry = {'host': host, 'filename': filename}

        if self.collection:
            self.json = self.collection.find_one_and_update({'basename': self.basename},
                    {'$addToSet': {'raw': entry}},
                    return_document=ReturnDocument.AFTER)

        return True

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

    def accessor(self):
        if hosts.is_old_nas(self.host):
            return remote.OldCovisNasAccessor(self)
        elif hosts.is_nas(self.host):
            return remote.CovisNasAccessor(self)
        elif hosts.is_dmas(self.host):
            return None

    def reader(self):
        return self.accessor().reader()
