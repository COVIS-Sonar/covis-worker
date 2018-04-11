
from covis_db.db import CovisDB

# These basenames are in the test data set
good_basenames = ["APLUWCOVISMBSONAR001_20100930T153416.845Z-DIFFUSE"]

# These basenames are valid but not in the test data set
bad_basenames = ["APLUWCOVISMBSONAR001_20141215T030021.657Z-IMAGING"]

def test_find_basenames():
    db = CovisDB()

    for bn in good_basenames:
        results = db.find(basename=bn)
        assert results
        assert len(results) == 1

    for bn in bad_basenames:
        results = db.find(basename=bn)
        assert results == []


def test_covis_run():

    db = CovisDB()

    results = db.find(basename=good_basenames[0])

    assert len(results) == 1

    run = results[0]
    assert run.mode == "DIFFUSE"

    assert run.raw.at("old-covis-nas") == False
    assert run.raw.at("dmas") == True
