

import os
import re

from minio import Minio
from minio.error import ResponseError


## Constant configuration for now...
old_covis_nas_hostname = os.getenv("OLD_COVIS_NAS_HOSTNAME","covis-data.apl.washington.edu")
old_covis_nas_minio_map = { 1: 9000,
                            2: 9001 }


re_old_covis_nas = re.compile( r"covis-nas\d", re.IGNORECASE)
re_covis_nas     = re.compile( r"covis-nas\Z", re.IGNORECASE)
re_dmas          = re.compile( r"dmas", re.IGNORECASE)

def site_to_re(site):
    if site == "dmas":
        return re_dmas
    elif site == "old-covis-nas":
        return re_old_covis_nas
    elif site == "covis-nas":
        return re_covis_nas
    else:
        raise "Don't recognise site" % site



class CovisRaw:

    def __init__(self,run,raw):
        self.run = run
        self.raw = raw

    def at(self,site):
        re = site_to_re(site)

        for r in self.raw:
            if re.match(r["host"]):
                return True

        return False

    def stream(self,source_prefs=['covis-nas',"old-covis-nas","dmas"]):

        for s in source_prefs:
            re = site_to_re(s)
            for r in self.raw:
                if re.match(r["host"]):
                    return self.stream_from(s,r)

        return None

    def stream_from(self,src,raw):
        if src=="dmas":
            return self.dmas_stream(raw)
        elif src=="old-covis-nas":
            return self.old_nas_stream(raw)
        elif src=="covis-nas":
            return self.nas_stream(raw)

    def old_nas_stream(self,raw):
        ## Which old NAS do I need?
        nas_id = re.search('(\d+)$', raw["host"]).group(0)

        if not nas_id.isdigit():
            return None

        nas_id = int(nas_id)
        port = old_covis_nas_minio_map[nas_id]

        if not port:
            return None

        full_hostname = "%s:%d" % (old_covis_nas_hostname, port)
        client = Minio(full_hostname,
                  access_key='covis',
                  secret_key='coviscovis')

        bucket = "raw"
        filename = "%04/%02d/%02d/%s.gz" % (self.run.datetime.year,
                        self.run.datetime.month, self.run.datetime.day,
                        self.raw['filename'])

        print("Looking for filename \"%s\"" % filename)

        return minioClient.get_object(bucket, filename)


    def nas_stream(self,raw):
        return None

    def dmas_stream(self,raw):
        return None
