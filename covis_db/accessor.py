

import os
import re
import pathlib

import boto3
import botocore

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


    @property
    def basename(self):
        return pathlib.Path(self.path).stem

    def minio_client(self):
        logging.debug("Accessing minio host: %s : %s : %s" % (self.url,self.access_key,self.secret_key))
        return Minio(self.url,
                  access_key=self.access_key,
                  secret_key=self.secret_key,
                  secure=False)

    def fget_object(self, file_path, object_name=None ):
        if not object_name: object_name = self.path
        logging.debug("Getting %s / %s to file %s" % (self.bucket, object_name, file_path ))
        return self.minio_client().fget_object( bucket_name=self.bucket, object_name=str(object_name), file_path=str(file_path) )


    def fput_object(self, file_path, object_name=None ):
        if not object_name: object_name = self.path
        logging.debug("Putting file %s to %s / %s" % (file_path, self.bucket, object_name ))
        return self.minio_client().fput_object( bucket_name=self.bucket, object_name=str(object_name), file_path=str(file_path) )

    def reader(self):
        logging.debug("Getting object at %s / %s" % (self.bucket, self.path))
        return self.minio_client().get_object(self.bucket, self.path)

    def write(self, io, length):
        logging.debug("Writing object to %s / %s" % (self.bucket, self.path))
        return self.minio_client().put_object(self.bucket, str(self.path), io, length)

    def stats(self, path = None):
        if not path: path = self.path
        return self.minio_client().stat_object(self.bucket, str(path) )

    def filesize(self):
        return self.stats().size

    def remove(self):
        return self.minio_client().remove_object(self.bucket, self.path)

    def exists(self, path=None):
        if not path: path = self.path
        try:
            stats = self.stats(str(path))
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



class WasabiNasAccessor(MinioAccessor):

    def __init__(self, raw):

        super().__init__(bucket="covis-raw",
                         path=raw.filename,
                         config_base=hosts.config_base(raw.host))


class WasabiAccessor:

    def __init__(self,
                path=None,
                config_base="WASABI"):

        self.access_key=config("%s_ACCESS_KEY"  % config_base )
        self.secret_key=config("%s_SECRET_KEY"  % config_base )
        self.bucket=config("%s_BUCKET" % config_base )

        self.path = path


    def boto_object(self):
        #logging.debug("Accessing Boto3 host: %s" % self.url)
        s3 = boto3.resource('s3',
                            endpoint_url = 'https://s3.wasabisys.com',
                            aws_access_key_id = self.access_key,
                            aws_secret_access_key = self.secret_key)
        return s3.Bucket( self.bucket ).Object( self.path )


    # def reader(self):
    #     logging.debug("Getting object at %s / %s" % (self.bucket, self.path))
    #     return self.boto_bucket().download_fileobj(self.bucket, self.path)
    #
    # def write(self, io, length):
    #     logging.debug("Writing object to %s / %s" % (self.bucket, self.path))
    #     return self.minio_client().put_object(self.bucket, str(self.path), io, length)

    def filesize(self):
        return self.boto_object().content_length

    # def remove(self):
    #     return self.minio_client().remove_object(self.bucket, self.path)
    #
    def exists(self):
        return self.filesize() != None




    #     try:
    #         stats = self.stats()
    #         return True
    #     except NoSuchKey:
    #         return False




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
