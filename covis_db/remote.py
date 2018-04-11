

import os
import re
import pathlib

from minio import Minio
from minio.error import ResponseError


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

    # Constant configuration for now...
    #old_covis_nas_hostname = os.getenv("OLD_COVIS_NAS_HOSTNAME","10.95.97.79") #covis-data.apl.washington.edu")
    old_covis_nas_minio_map = { 1: 9001,
                                2: 9002 }

    def __init__(self,run,raw):
        self.run = run
        self.raw = raw

    def old_covis_nas_hostname(self):
        return "localhost"
#        return "10.95.97.79"

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
        port = self.old_covis_nas_minio_map[nas_id]

        if not port:
            return None

        full_hostname = "%s:%d" % (self.old_covis_nas_hostname(), port)
        #print("Accessing minio host: %s" % full_hostname)

        client = Minio(full_hostname,
                  access_key='covis',
                  secret_key='coviscovis',
                  secure=False)

        bucket = "raw"
        # filename = "/".join([ "%04d" % self.run.datetime.year,
        #                       "%02d" % self.run.datetime.month,
        #                       "%02d" % self.run.datetime.day,
        #                       raw['filename']])

        p = pathlib.Path(raw['filename'])
        filename = "/".join(p.parts[3:])

        #print("Looking for filename \"%s\"" % filename)

        return client.get_object(bucket, filename)


    def nas_stream(self,raw):
        return None

    def dmas_stream(self,raw):
        return None
