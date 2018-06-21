
import pathlib
import re


def make_basename(file):

    base = str(pathlib.PurePath(file).stem)

    base = re.sub(r'\.tar','',base)

    return base
