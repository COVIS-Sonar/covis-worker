
from covis_db import db, remote
from decouple import config

# These basenames are in the test data set
exists_on_old_nas = ["APLUWCOVISMBSONAR001_20111001T010000.049Z-DIFFUSE"]

not_on_nas = ["APLUWCOVISMBSONAR001_20111001T125923.044Z-DIFFUSE"]


def test_not_in_minio():
    covis = db.CovisDB()
    result = covis.find( basename=not_on_nas[0])

    assert result.mode == "DIFFUSE"
    accessor = result.raw[0].accessor()
    assert False == accessor.exists()


def test_covis_raw():

    covis = db.CovisDB()
    result = covis.find( basename=exists_on_old_nas[0])

    assert result.mode == "DIFFUSE"

    #assert result.raw.at("old-covis-nas") == True

    accessor = result.raw[0].accessor()

    assert accessor.exists()

    f = accessor.reader()
    assert f



    # We expect f to be a urllib3.response.HTTPResponse
    assert int(f.info()["Content-Length"]) == 2928961



def test_covis_copy_minio_to_minio():

    covis = db.CovisDB()

    result = covis.find( basename=exists_on_old_nas[0])

    assert result.mode == "DIFFUSE"

    with result.raw[0].reader() as src:
        nas = remote.CovisNasAccessor(result.raw[0])
        nas.write(src, int(src.getheader('Content-Length')))
