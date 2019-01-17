

import os
import re
import pathlib

from decouple import config

import logging

from . import hosts

from minio import Minio
from minio.error import ResponseError, NoSuchKey

from io import BytesIO

import requests


class MinioAccessor:

    def __init__(self,
                bucket=None,
                path=None,
                config_base=""):

        self.access_key=config("%s_ACCESS_KEY"  % config_base )
        self.secret_key=config("%s_SECRET_KEY"  % config_base )
        self.url = config("%s_URL" % config_base )

        logging.debug("Using minio url %s" % self.url)

        self.bucket = bucket
        self.path = path


    # def host(self):
    #     return self._host
    #
    # def port(self):
    #     return self._port


    def minio_client(self):
        logging.debug("Accessing minio host: %s" % self.url)
        return Minio(self.url,
                  access_key=self.access_key,
                  secret_key=self.secret_key,
                  secure=False)

    def reader(self):
        logging.debug("Getting object at %s / %s" % (self.bucket, self.path))
        return self.minio_client().get_object(self.bucket, self.path)

    def write(self, io, length):
        logging.debug("Writing object to %s / %s" % (self.bucket, self.path))
        return self.minio_client().put_object(self.bucket, str(self.path), io, length)

    def stats(self):
        return self.minio_client().stat_object(self.bucket, self.path)

    def remove(self):
        return self.minio_client().remove_object(self.bucket, self.path)

    def exists(self):
        try:
            stats = self.stats()
            return True
        except NoSuchKey:
            return False

# re_old_covis_nas = re.compile( r"old-covis-nas(\d+)", re.IGNORECASE)

class CovisNasAccessor(MinioAccessor):

    def __init__(self, raw):

        super().__init__(bucket="raw",
                         path=raw.filename,
                         config_base=hosts.config_base(raw.host))


class OldCovisNasAccessor(CovisNasAccessor):

    def __init__(self, raw):
        super().__init__(raw)

    def write(self, io):
        raise "Can't write to the old covis NAS"



class DmasAccessor:

    '''Uses ONC Oceans 2.0 API:
         https://wiki.oceannetworks.ca/display/O2A/Oceans+2.0+API+Home
    '''

    def __init__(self,
                path=None):

        self.dmas_key=config("DMAS_API_KEY" )
        self.path = path

        logging.info("Accessing DMAS for %s" % self.path)

    def reader(self):

        logging.debug("Getting object %s from DMAS" % self.path)

        params = {'method': 'getFile',
                    'token': self.dmas_key,
                    'filename': self.path }

        r = requests.get("https://data.oceannetworks.ca/api/archivefiles", params=params)

        ## As a shortcut, throw an exception if status is bad
        r.raise_for_status()

        return BytesIO(r.content)
