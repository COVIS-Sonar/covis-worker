
from covis_db import db, accessor
from decouple import config

from os import stat

# These basenames are in the test data set
exists_on_old_nas = ["APLUWCOVISMBSONAR001_20111001T215909.172Z-DIFFUSE"]

## This needs to exist in the db but not in  covis-test-data/old-covis-nas1
not_on_nas = ["APLUWCOVISMBSONAR001_20111001T125923.044Z-DIFFUSE"]


# def test_not_in_minio():
#     covis = db.CovisDB()
#     result = covis.find( basename=not_on_nas[0])
#
#     assert result
#     assert result.mode == "DIFFUSE"
#
#     # accessor = raw.accessor()
#     # assert False == accessor.exists()


def test_covis_raw():

    covis = db.CovisDB()
    result = covis.find( basename=exists_on_old_nas[0])

    assert result
    assert result.mode == "DIFFUSE"

    raw = next(x for x in result.raw if x.host=='OLD-COVIS-NAS1')

    accessor = raw.accessor()
    assert accessor.exists()

    f = accessor.reader()
    assert f

    # We expect f to be a urllib3.response.HTTPResponse
    fileinfo = stat( 'covis-test-data/old-covis-nas1/raw/2011/10/01/APLUWCOVISMBSONAR001_20111001T215909.172Z-DIFFUSE.tar.gz')
    assert int(f.info()["Content-Length"]) == fileinfo.st_size



def test_covis_copy_minio_to_minio():

    covis = db.CovisDB()

    result = covis.find( basename=exists_on_old_nas[0])

    assert result
    assert result.mode == "DIFFUSE"

    raw = next(x for x in result.raw if x.host=='OLD-COVIS-NAS1')

    with raw.reader() as src:
        nas = accessor.CovisNasAccessor(result.raw[0])
        nas.write(src, int(src.getheader('Content-Length')))
