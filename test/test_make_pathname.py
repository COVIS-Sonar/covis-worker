
import pytest

from covis_db import misc

# These basenames are in the test data set
good_filenames = {"/tmp/tmp7b0c134s/APLUWCOVISMBSONAR001_20120626T154808.006Z-DIFFUSE.7z": "2012/06/26/APLUWCOVISMBSONAR001_20120626T154808.006Z-DIFFUSE.7z"}

# Malformed filesnames
#bad_filenames = {"APLUWCOVISMBSONAR001_20101012T211404.7z": "APLUWCOVISMBSONAR001_20101012T213802.272Z-DOPPLER.7z" }

def test_make_pathname():

    for input,output in good_filenames.items():
        assert misc.make_pathname(input, suffix='.7z') == output

    # for input,output in bad_filenames.items():
    #     assert misc.make_pathname(input, suffix='.7z') == output
