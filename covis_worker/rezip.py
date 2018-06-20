from __future__ import absolute_import, unicode_literals
from .celery import app

@app.task
def rezip(basename, dest_host, dest_fmt='7z', src_host=[], tempdir=None):
    print("Rezipping %s" % basename)
