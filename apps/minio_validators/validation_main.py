

from covis_db import db,hosts,remote,misc


from minio_validators.fix_malformed_filenames_2019_01 import fix_malformed_filenames_2019_01



def do_validate( args, host, client, mio, filename ):

    basename = misc.make_basename(filename)

    if basename==filename:
        print("I think a basename was specified instead of a filename!")
        return

    print("")
    print("Object \"%s\"; basename \"%s\"" % (filename, basename))

    #print("Checking database for basename %s" % basename)
    run = client.find(basename)

    ## 2019-01-15.   Check for malformed filenames of
    ## "APLUWCOVISMBSONAR001_20150429T111015.7z" rather than
    ## "APLUWCOVISMBSONAR001_20150429T111015.629Z-DIFFUSE.7z"
    if fix_malformed_filenames_2019_01.isbad( basename ):
        fix_malformed_filenames_2019_01.fix(client, mio, basename)
        return


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
                return

            run.add_raw(host,filename)

    #
    # count = count -1
    # if count <= 0:
    #     exit()
