

import os
import re
import pathlib

from decouple import config


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

        self.bucket = bucket
        self.path = path

    # def host(self):
    #     return self._host
    #
    # def port(self):
    #     return self._port


    def minio_client(self):
        print("Accessing minio host: %s" % self.url)
        return Minio(self.url,
                  access_key=self.access_key,
                  secret_key=self.secret_key,
                  secure=False)

    def reader(self):
        print("Getting object at %s / %s" % (self.bucket, self.path))
        return self.minio_client().get_object(self.bucket, self.path)

    def write(self, io, length):
        print("Writing object to %s / %s" % (self.bucket, self.path))
        return self.minio_client().put_object(self.bucket, self.path, io, length)

    def stats(self):
        return self.minio_client().stat_object(self.bucket, self.path)

    def exists(self):
        try:
            stats = self.stats()
            return True
        except NoSuchKey:
            return False

re_old_covis_nas = re.compile( r"old-covis-nas(\d+)", re.IGNORECASE)

class OldCovisNasAccessor(MinioAccessor):

    def __init__(self, raw):

        # Identify which old nas
        m = re_old_covis_nas.search(raw.host)
        self.num = int(m.group(1))

        ## Error checking here

        print("Accessing old covis nas %d" % self.num)

        super().__init__(bucket="raw",
                         path=raw.filename,
                         config_base="OLD_NAS%d" % self.num)

    def write(self, io):
        raise "Can't write to the old covis NAS"

class CovisNasAccessor(MinioAccessor):

    def __init__(self, raw):

        super().__init__(bucket="raw",
                         path=raw.filename,
                         config_base="NAS")



# re_old_covis_nas = re.compile( r"old-covis-nas\d", re.IGNORECASE)
# re_covis_nas     = re.compile( r"covis-nas\Z", re.IGNORECASE)
# re_dmas          = re.compile( r"dmas", re.IGNORECASE)


# def site_to_re(site):
#     if site == "dmas":
#         return re_dmas
#     elif site == "old-covis-nas":
#         return re_old_covis_nas
#     elif site == "covis-nas":
#         return re_covis_nas
#     else:
#         raise "Don't recognise site" % site


#
#     def stream(self,source_prefs=['covis-nas',"old-covis-nas","dmas"]):
#
#         for s in source_prefs:
#             re = site_to_re(s)
#             for r in self.raw:
#                 if re.match(r["host"]):
#                     return self.stream_from(s,r)
#
#         return None
#
#     def stream_from(self,src,raw):
#         if src=="dmas":
#             return self.dmas_stream(raw)
#         elif src=="old-covis-nas":
#             return self.old_nas_stream(raw)
#         elif src=="covis-nas":
#             return self.nas_stream(raw)
#
#     def old_nas_stream(self,raw):
#         ## Which old NAS do I need?
#         print(raw["host"])
#
#
#
#         if not port:
#             return None
#
#         full_hostname = "%s:%d" % (self.old_covis_nas_hostname(), port)
#         print("Accessing minio host: %s" % full_hostname)
#
#         client = Minio(full_hostname,
#                   access_key='covis',
#                   secret_key='coviscovis',
#                   secure=False)
#
#         bucket = "raw"
#         # filename = "/".join([ "%04d" % self.run.datetime.year,
#         #                       "%02d" % self.run.datetime.month,
#         #                       "%02d" % self.run.datetime.day,
#         #                       raw['filename']])
#
#         p = pathlib.Path(raw['filename'])
#         filename = "/".join(p.parts[3:])
#
#         print("Looking for filename \"%s\"" % filename)
#
#         return client.get_object(bucket, filename)
#
#
#     def nas_stream(self,raw):
#         return None
#
#     def dmas_stream(self,raw):
#         return None
