

import re

class fix_malformed_filenames_2019_01:

    def isbad( basename ):
        if re.match( r'APLUWCOVISMBSONAR001[\_\-]\d{8}T\d{6}$', basename ):
            return True

        return False

    def fix( client, mio, basename ):

        print("!!! Basename is malformed")

        ## Check for existing filename
        result = client.runs.find_one({'basename': {'$regex': basename + '.*'}})
        if result:
            print("!!! Found redundant entry with basename '%s'" % result['basename'])

            if fix_malformed_filenames_2019_01.isbad( result['basename'] ):
                 print('!!! !!! But other entry is malformed as well')
                 return


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

                    ## Surely this isn't efficient?
                    print("FIX: Removing previous entries...")
                    result = client.runs.find_one_and_update({'basename': new_basename},
                                                        {'$pull': {'raw': {'host': host}}} )

                    print("FIX: Updated entry with filename %s" % correct_filename)
                    result = client.runs.find_one_and_update({'basename': new_basename},
                                                         {'$push': {'raw': {'host': host, 'filename': correct_filename }}} )
