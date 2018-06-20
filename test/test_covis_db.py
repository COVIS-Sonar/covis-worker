
import pytest

# These basenames are in the test data set
good_basenames = ["APLUWCOVISMBSONAR001_20100930T153416.845Z-DIFFUSE"]

# These basenames are valid but not in the test data set
bad_basenames = ["APLUWCOVISMBSONAR001_20140226T090039.177Z-IMAGING"]


def test_find_basenames(covisdb):
    for bn in good_basenames:
        result = covisdb.find(basename=bn)
        assert result

    for bn in bad_basenames:
        result = covisdb.find(basename=bn)
        assert not result

def test_covis_run(covisdb):
    result = covisdb.find(basename=good_basenames[0])
    assert result

    assert result.mode == "DIFFUSE"

    # assert result.raw.at("old-covis-nas") == False
    # assert result.raw.at("dmas") == True


def test_covis_add(covisdb):
    run = covisdb.find(basename=good_basenames[0])
    assert run

    raw = run.raw[0]

    assert(raw)

    assert run.find_raw( raw.host, raw.filename )
    assert run.find_raw('COVIS-NAS', raw.filename ) == False

    assert len(run.raw) == 1

    # This should fail
    assert run.add_raw(raw.host, raw.filename) == False

    # This should succeed
    assert run.add_raw('COVIS-NAS', raw.filename)
    assert len(run.raw) == 2

    # Attempt to add again should fail
    assert run.add_raw('COVIS-NAS', raw.filename) == False
    assert len(run.raw) == 2

    assert run.find_raw( raw.host, raw.filename )
    assert run.find_raw( 'COVIS-NAS', raw.filename )

    # covisdb.update(basename=good_basenames[0], run=run)

    ## Check that it's in the db
    r = covisdb.find(basename=good_basenames[0])

    # Find the raw
    assert len(run.raw) == 2
    assert r.find_raw( raw.host, raw.filename )
    assert r.find_raw( 'COVIS-NAS', raw.filename )
