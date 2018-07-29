#!/usr/bin/env python

from distutils.core import setup

setup(name='covis_worker',
      version='0.1',
      description='',
      author='Aaron Marburg',
      author_email='amarburg@apl.washington.edu',
      url='',
      packages=['covis_db','covis_worker'],
      install_requires=['minio','pymongo','libarchive',
                        'python-decouple','paramiko','boto3','sendgrid']
     )
