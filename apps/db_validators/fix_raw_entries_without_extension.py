
import logging
from datetime import datetime

from covis_db import db,hosts,remote,misc

def fix_raw_entries_without_extension( args, run ):

    for raw in run.raw:
        if( raw.host == "DMAS" ):
            continue

        # Look for a specific known problem where raw filenames
        # on covis-nas don't have the .7z extension
        if is_nas(raw.host) and re.match(r'^(?!.*[.]7z$).*$',raw.filename):
            logging.info("!!! found file on COVIS-NAS without extention")

            if args.fix:
                logging.info("     (fix goes here)")
