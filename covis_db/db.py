
from pymongo import MongoClient,ReturnDocument
import re

from decouple import config

from . import remote


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

    def find(self, basename=None):
        if basename:
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
        for f in self.raw:
            if f.host == host and f.filename == filename:
                return CovisRaw(f)
        return False

    def add_raw(self,host,filename):
        if self.find_raw(host,filename):
            return False

        print("Before:", self.json)

        # TODO:  Validate hostname

        entry = {'host': host, 'filename': filename}
        self.json = self.collection.find_one_and_update({'basename': self.basename},
                    {'$addToSet': {'raw': entry}},
                    return_document=ReturnDocument.AFTER)

        print("After:",self.json)
        return True

re_old_covis_nas = re.compile( r"old-covis-nas\d", re.IGNORECASE)
#re_covis_nas     = re.compile( r"covis-nas\Z", re.IGNORECASE)
#re_dmas          = re.compile( r"dmas", re.IGNORECASE)


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
        if re_old_covis_nas.match(self.host):
            return remote.OldCovisNasAccessor(self)
        elif self.host == "COVIS-NAS":
            return None
        elif self.host == "DMAS":
            return None

    def reader(self):
        return self.accessor().reader()
