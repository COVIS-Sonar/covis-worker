
from pymongo import MongoClient
import re

from . import remote

# Thin wrapper around MongoDB client accessor
#
#
class CovisDB:

    def __init__(self, db_client = None):

        if db_client:
            self.client = db_client
        else:
            self.client = MongoClient()

        self.db = self.client.covis
        self.runs = self.db.runs

    def find( self, basename=None ):
        if basename:
            return self.find_by_basename(basename)

    def find_by_basename(self, basename):
        print("Searching for basename: %s" % (basename))

        # Expect small returns, so unwrap
        r = self.runs.find_one({'basename': basename})

        if r:
            return CovisRun(r)
        else:
            return None

class CovisRun:

    def __init__(self, json):
        self.json = json

    @property
    def datetime(self):
        return self.json["datetime"]

    @property
    def mode(self):
        return self.json["mode"]

    @property
    def raw(self):
        return CovisRaw(self.json["raw"])


class CovisRaw:

    def __init__(self,raw):
        self.raw = raw

    # def at(self,site):
    #     re = site_to_re(site)
    #
    #     for r in self.raw:
    #         if re.match(r["host"]):
    #             return True
    #
    #     return False
