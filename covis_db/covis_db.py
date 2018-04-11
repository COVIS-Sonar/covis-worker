
from pymongo import MongoClient


def foobar():
    print("Hello!")

class CovisDB:

    def __init__( self, db_client = None ):

        if db_client:
            self.client = db_client
        else:
            self.client = MongoClient()

        self.db = self.client.covis
        self.runs = self.db.runs

    def find( self, basename ):
        if basename:
            self.find_by_basename(basename)

    def find_by_basename( self, basename ):
        return self.runs.find( {"basename": basename})
