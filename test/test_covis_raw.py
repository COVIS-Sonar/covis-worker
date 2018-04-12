
from covis_db import db

# These basenames are in the test data set
basename_on_nas = ["APLUWCOVISMBSONAR001_20111001T010000.049Z-DIFFUSE"]

def test_covis_raw(monkeypatch):

    monkeypatch.setattr('covis_db.remote.OldCovisNasAccessor.hostname', lambda x: "localhost")

    covis = db.CovisDB()

    result = covis.find( basename=basename_on_nas[0])

    assert result.mode == "DIFFUSE"

    #assert result.raw.at("old-covis-nas") == True

    f = result.raw[0].reader()

    assert f

    # We expect f to be a urllib3.response.HTTPResponse
    assert int(f.info()["Content-Length"]) == 2928961
