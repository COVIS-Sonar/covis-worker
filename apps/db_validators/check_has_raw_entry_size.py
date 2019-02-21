
import logging

from covis_db import db,hosts,remote,misc

def check_has_raw_entry_size( args, run ):
    logging.info("   Checking raw sizes for run %s" % run.basename)

    for raw in run.raw:
        if raw and (hosts.is_nas( raw.host ) or hosts.is_wasabi( raw.host )):
            filesize = raw.accessor().filesize()

            if raw.filesize and raw.filesize == filesize:
                logging.info("   ... On host %s, raw entry size is correct (%d)" % (raw.host, raw.filesize))
                return True

            logging.info("   !!! On host %s, Raw entry size is incorrect or does not exist (%s != %s)" % (raw.host, raw.filesize, filesize))

            if args.fix:
                logging.info("Fixing")
                raw.json["filesize"] = filesize
                run.update_raw( raw.json )

    return True
