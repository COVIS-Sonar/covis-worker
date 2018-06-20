
from pymongo import MongoClient,ReturnDocument
import re

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
            return CovisRun(self.runs, r)
        else:
            return None


class CovisRun:

    def __init__(self, collection, json):
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

        print("Before:", self.json)

        entry = {'host': host, 'filename': filename}
        self.json = self.collection.find_one_and_update({'basename': self.basename},
                    {'$addToSet': {'raw': entry}},
                    return_document=ReturnDocument.AFTER)

        return True


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
            return None
        elif hosts.is_dmas(self.host):
            return None

    def reader(self):
        return self.accessor().reader()
