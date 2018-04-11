
from pymongo import MongoClient


class CovisDB:

    def __init__( self, db_client = None ):

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
        print("Searching for basename: %s" % basename)

        ## Expect small returns, so unwrap
        cursor = self.runs.find( {'basename': basename})

        return [p for p in cursor]
