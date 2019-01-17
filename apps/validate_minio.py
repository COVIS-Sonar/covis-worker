#!/usr/bin/env python3

from pprint import pprint
import argparse
import sys
import json
import pathlib
import logging

from pymongo import MongoClient
from decouple import config
from covis_db import db,hosts,remote,misc

from minio.error import ResponseError, NoSuchKey

from validators.fix_malformed_filenames_2019_01 import fix_malformed_filenames_2019_01


parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', default=config('MONGODB_URL', default="mongodb://localhost/"),
                    help='URL (mongodb://hostname/) of MongoDB host')

parser.add_argument('--dry-run', action='store_true')

parser.add_argument('--fix', action='store_true')

parser.add_argument('hosts', nargs='*', default=["covis-nas"],
                    help='Minio hostname...')

parser.add_argument('--log', metavar='log', nargs='?',
                    default=config('LOG_LEVEL', default='INFO'),
                    help='Logging level')

args = parser.parse_args()

client = db.CovisDB(MongoClient(args.dbhost))
logging.basicConfig( level=args.log.upper() )


#count = 200

for host in args.hosts:

    host = host.upper()

    if not hosts.validate_host(host):
        logging.warning("Host \"%s\" is not a valid covis host" % host)
        continue

    ## Should DRY this
    raw = db.CovisRaw({"host":host, "filename":""})
    accessor = raw.accessor()

    if not accessor:
        logging.warning("Unable to create accessor to %s" % host)
        continue

    mio = accessor.minio_client()
    objects = mio.list_objects( accessor.bucket, recursive=True )

    for obj in objects:
        # print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
        #         obj.etag, obj.size, obj.content_type)

        filename = str(obj.object_name)
        basename = misc.make_basename(filename)

        print("")
        print("Object \"%s\"; basename \"%s\"" % (filename, basename))

        #print("Checking database for basename %s" % basename)
        run = client.find(basename)

        ## 2019-01-15.   Check for malformed filenames of
        ## "APLUWCOVISMBSONAR001_20150429T111015.7z" rather than
        ## "APLUWCOVISMBSONAR001_20150429T111015.629Z-DIFFUSE.7z"
        if fix_malformed_filenames_2019_01.isbad( basename ):
            print("!!! Basename is malformed")

            ## Check for existing filename
            result = client.runs.find_one({'basename': {'$regex': basename + '.*'}})
            if result:
                print("!!! Found redundant entry with basename '%s'" % result['basename'])

                if fix_malformed_filenames_2019_01.isbad( result['basename'] ):
                     print('!!! !!! But other entry is malformed as well')
                     continue


                ## Check for existence of properly named file in Minio
                correct_filename = misc.make_pathname( result['basename'], suffix = '.7z' )
                print("Checking for correctly name file '%s'" % correct_filename)

                try:
                    mio.get_object( accessor.bucket, correct_filename )
                    print("!!! Correct file exists, deleting mis-named copy")
                    if args.fix:
                        print("FIX: Deleted mis-named one")
                        mio.remove_object(accessor.bucket, obj.object_name)

                except NoSuchKey as err:
                    print("!!! Does not exist, renaming ...")

                    if args.fix:
                        # src_path needs to include source bucket
                        src_path = "%s/%s" % (accessor.bucket,obj.object_name)
                        print("FIX: Copying %s to %s" % (src_path, correct_filename))

                        copy_result = mio.copy_object(accessor.bucket, correct_filename, src_path )
                        print(copy_result)

                        print("FIX: Removing object %s" % obj.object_name)
                        remove_result = mio.remove_object(accessor.bucket, obj.object_name)
                        print(remove_result)

                        new_basename = misc.make_basename(correct_filename)
                        # run = client.find(new_basename)

                        print("FIX: Removing previous entries...")
                        result = client.runs.find_one_and_update({'basename': new_basename},
                                                            {'$pull': {'raw': {'host': host}}} )

                        print("FIX: Updated entry with filename %s" % correct_filename)
                        result = client.runs.find_one_and_update({'basename': new_basename},
                                                             {'$push': {'raw': {'host': host, 'filename': correct_filename }}} )

            continue

            #fix_malformed_filenames_2019_01.fix( client, run, args )

        ## Standard QC path
        if run:

            ## Remove these extraneous fields
            if 'host' in run.json:
                if args.fix:
                    print("!!! has extraneous 'host' field, removing")
                    run.collection.find_one_and_update({'basename': run.basename},
                                                        {'$unset': {'host':""}})
                else:
                    print("!!! has extraneous 'host' field, specify --fix to fix")


            if 'filename' in run.json:
                if args.fix:
                    print("!!! has extraneous 'filename' field, removing")
                    run.collection.find_one_and_update({'basename': run.basename},
                                                        {'$unset': {'filename':""}})
                else:
                    print("!!! has extraneous 'filename' field, specify --fix to fix")


            raw = run.find_raw( host )

            if raw:
                print("... exists in database and has raw for host %s" % host)

                if raw.filename != filename:
                    print("!!! db filename '%s' do not match expected '%s'" % (raw.filename,filename))

                    if args.fix:
                        run.collection.find_one_and_update({'basename': basename},
                                                            {'$pull': {'raw': {'host': host}}} )

                        print("FIX: Updated entry with filename %s" % filename)
                        run.collection.find_one_and_update({'basename': basename},
                                                             {'$addToSet': {'raw': {'host': host, 'filename': filename }}} )



            else:
                print("!!! but does not have raw entry for host %s." % host)

                if args.fix:
                    print("FIX:   Adding raw entry for %s to database" % host)
                    run.add_raw(host,filename)

        else:
            print("!!! Basename %s is not in database" % basename)

            if args.fix:
                print("FIX: Adding run for %s" % basename)
                run = client.add_run(basename)

                if not run:
                    print("FIX:   Error adding run for basename %s" % basename)
                    continue

                run.add_raw(host,filename)

        #
        # count = count -1
        # if count <= 0:
        #     exit()
