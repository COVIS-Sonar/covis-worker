

from covis_db import remote

import shutil
import logging
import tempfile
import tarfile

from os import getenv
from pathlib import Path

## This is a 12M file
dmas_filenames = ["APLUWCOVISMBSONAR001_20101001T042617.821Z-DIFFUSE.tar"]

def test_retrieve_dmas():

    if not getenv('DMAS_API_KEY'):
        logging.error("DMAS_API_KEY not set, skipping test_retrieve_dmas.")
        return

    with tempfile.TemporaryDirectory() as tempdir:

        for d in dmas_filenames:

            output = Path(tempdir) / d

            access = remote.DmasAccessor(d)
            assert(access)

            r = access.reader()
            assert(r)

            with open(output,'wb') as outfile:
                shutil.copyfileobj(r, outfile)

            ## Validate output
            stat = output.stat()
            assert( stat.st_size > 0 )

            # errorlevel=2 causes any tar errors to result in an exception
            with tarfile.open(output,errorlevel=2) as tf:
                assert(tf)

                members = tf.getmembers()

                ## This is known apriori for this DMAS file
                assert( len(members) == 26 )
