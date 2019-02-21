
import logging
from datetime import datetime

from covis_db import db,hosts,remote,misc

def add_raw_entry_for_wasabi( args, run ):

    if run.datetime < datetime(2018,1,1):
        return True

    logging.info("   Checking for Wasabi raw for basename %s" % run.basename)

    ## Check for raw
    if run.find_raw("WASABI"):
        logging.info("... Has raw entry for WASABI")
        return True

    if args.fix:
        s3_file = misc.make_pathname( run.basename, suffix=".tar.gz" )
        logging.info("    Checking Wasabi for %s" % s3_file)

        try:
            accessor = remote.WasabiAccessor( path=s3_file )

            filesize = accessor.filesize()
            logging.info("    File %s on wasabi is %d" % (run.basename, filesize) )

            if not run.add_raw("WASABI", s3_file, filesize=filesize, suffix=".tar.gz"):
                logging.info("      Unable to add raw")

            logging.info("  ... done adding")
        except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                logging.warning(message)
                return False

    return True
