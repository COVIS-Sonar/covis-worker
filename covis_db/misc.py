import pathlib
import re
from os import path

from datetime import datetime
from pathlib import Path

def is_covis_file(filename):
    return is_endeavour_file(filename) or is_ashes_file(filename)

def is_endeavour_file(filename):
    return re.match(r'APLUWCOVISMB.*', filename)

def is_ashes_file(filename):
    return re.match(r'^COVIS-*', filename)


# This is essentially "make stem" but is smart about removing .tar
# if it is also part of the name:
#
#    foo.7z      -> foo
#    foo.tgz     -> foo
#    foo.tar.gz  -> foo
def make_basename(file):

    base = path.basename(file)
    base = re.sub(r'\.[\w\.]{2,6}$','',base)

    return base

def splitext(path):
    for ext in ['.tar.gz', '.tar.bz2']:
        if path.endswith(ext):
            return path[:-len(ext)], path[-len(ext):]
    return os.path.splitext(path)

def split_basename(basename):
    parts = re.split(r'[\_\-]', basename)

    # Todo:  More validation of parts

    # full timestamp with milliseconds
    match = re.match(r"\d{4}\d{2}\d{2}T\d{2}\d{2}\d{2}\.\d+Z", parts[1])
    if match:
        date = datetime.strptime(parts[1], "%Y%m%dT%H%M%S.%fZ")
    else:
        date = datetime.strptime(parts[1], "%Y%m%dT%H%M%S")

    if len(parts) > 2:
        mode = parts[2]
    else:
        mode = "(unknown)"

    return [date,mode]

def make_pathname( basename, date=None, suffix=None ):

    bname = make_basename(basename)

    if not date:
        date,mode = split_basename(bname)

    out = date.strftime("%Y/%m/%d/") + bname

    if suffix:
        out = out + suffix

    return out
