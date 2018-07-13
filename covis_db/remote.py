

import os
import re
import pathlib

from decouple import config

import logging

from . import hosts

from minio import Minio
from minio.error import ResponseError, NoSuchKey


class MinioAccessor:

    def __init__(self,
                bucket=None,
                path=None,
                config_base=""):

        self.access_key=config("%s_ACCESS_KEY"  % config_base )
        self.secret_key=config("%s_SECRET_KEY"  % config_base )
        self.url = config("%s_URL" % config_base )

        logging.info("Using minio url %s" % self.url)

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
        return self.minio_client().put_object(self.bucket, self.path, io, length)

    def stats(self):
        return self.minio_client().stat_object(self.bucket, self.path)

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
