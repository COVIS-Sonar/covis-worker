
from covis_db.db import CovisDB

# These basenames are in the test data set
good_basenames = ["APLUWCOVISMBSONAR001_20100930T153416.845Z-DIFFUSE"]

# These basenames are valid but not in the test data set
bad_basenames = ["APLUWCOVISMBSONAR001_20140226T090039.177Z-IMAGING"]

def test_find_basenames():
    db = CovisDB()

    for bn in good_basenames:
        result = db.find(basename=bn)
        assert result

    for bn in bad_basenames:
        result = db.find(basename=bn)
        assert not result

def test_covis_run():

    db = CovisDB()

    result = db.find(basename=good_basenames[0])

    assert result

    assert result.mode == "DIFFUSE"

    # assert result.raw.at("old-covis-nas") == False
    # assert result.raw.at("dmas") == True
