
from covis_db import covis_db

# These basenames are in the test data set
basename_on_nas = ["APLUWCOVISMBSONAR001_20111001T010000.049Z-DIFFUSE"]

def test_covis_run():

    db = covis_db.CovisDB()

    results = db.find( basename=basename_on_nas[0])

    assert len(results) == 1

    run = results[0]
    assert run.mode() == "DIFFUSE"

    assert run.raw.at("old-covis-nas") == True
