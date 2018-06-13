from __future__ import absolute_import, unicode_literals
from .celery import app

@app.task
def rezip(basename, dest, dest_fmt='7z', tempdir=None):
