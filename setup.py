#!/usr/bin/env python

from distutils.core import setup

setup(name='covis_db',
      version='0.1',
      description='',
      author='Aaron Marburg',
      author_email='amarburg@apl.washington.edu',
      url='',
      packages=['covis_db'],
      install_requires=['minio','pymongo']
     )
