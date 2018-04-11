
from covis_db.db import CovisDB
import covis_db.remote

# These basenames are in the test data set
basename_on_nas = ["APLUWCOVISMBSONAR001_20111001T010000.049Z-DIFFUSE"]

def test_covis_raw(monkeypatch):

    monkeypatch.setattr('covis_db.remote.CovisRaw.old_covis_nas_hostname', lambda x: "localhost")

    db = CovisDB()

    results = db.find( basename=basename_on_nas[0])

    assert len(results) == 1

    run = results[0]
    assert run.mode == "DIFFUSE"

    assert run.raw.at("old-covis-nas") == True

    f = run.raw.stream()

    assert f

    # We expect this to be a urllib3.response.HTTPResponse
    assert int(f.info()["Content-Length"]) == 2928961
