import pathlib
import re

def is_covis_file(filename):
    return is_endeavour_file(filename) or is_ashes_file(filename)

def is_endeavour_file(filename):
    return re.match(r'APLUWCOVISMB.*', filename)

def is_ashes_file(filename):
    return re.match(r'^COVIS-*', filename)

def make_basename(file):
    base = str(pathlib.PurePath(file).stem)
    base = re.sub(r'\.tar','',base)
    return base
