


import logging

from covis_db import db,hosts,remote,misc

def check_host_filename_at_top_level( args, run ):

    ## Drop entries where "host" and "filename" fields were inadvertantly added to top-level JSON
    if "filename" in run.json:
        logging.info("!!! Fixing raw entry ")

        # Pull bad entry
        result = run.collection.update_one({'basename': run.basename},
                                            {'$pull': {"raw" : { "host" : "COVIS-NAS"  }}} )

        result = run.collection.update_one({'basename': run.basename},
                                        {'$push': {"raw" : { "host" : "COVIS-NAS", "filename": run.json["filename"][0] }} })

        result = run.collection.update_one({'basename': run.basename},
                                        {'$unset': { "filename": "", "host": ""}})
