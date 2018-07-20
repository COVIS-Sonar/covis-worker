import pytest
from covis_db.db import CovisDB
from bson import json_util



# conftest.py is automatically imported by pytest

@pytest.fixture
def covisdb():
    db = CovisDB()
    db.db.drop_collection('runs')

    data = open('test/data/dump.json').read()
    jdata = json_util.loads(data)
    db.db.runs.insert_many(jdata)

    return db
