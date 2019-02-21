import logging

from covis_db import db,hosts,remote,misc

def check_duplicates( args, run ):

    cursor = run.collection.find({'basename': run.basename})

    logging.info("    Basename has %d entries" % cursor.count() )
    if cursor.count() > 1:
        logging.info("   !!! Multiple entries for %s" % run.basename)

        dups = [i["_id"] for i in cursor]
        print(dups)

        dups.pop(0)
        print(dups)

        if args.fix:
            logging.info("   >>> Fixing")

            for entry in dups:
                run.collection.remove( {"_id": entry } )
