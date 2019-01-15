
import pytest

from covis_db import misc

# These basenames are in the test data set
good_filenames = {"/tmp/tmp7b0c134s/APLUWCOVISMBSONAR001_20120626T154808.006Z-DIFFUSE.7z": "APLUWCOVISMBSONAR001_20120626T154808.006Z-DIFFUSE",
                    "APLUWCOVISMBSONAR001_20120626T154808.006Z-DIFFUSE.tar.gz":            "APLUWCOVISMBSONAR001_20120626T154808.006Z-DIFFUSE",
                    "APLUWCOVISMBSONAR001_20100930T160017.800Z-IMAGING":                   "APLUWCOVISMBSONAR001_20100930T160017.800Z-IMAGING"}


def test_make_basename():

    for input,output in good_filenames.items():
        assert misc.make_basename(input) == output
