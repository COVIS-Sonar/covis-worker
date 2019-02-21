
from covis_db import db,hosts,remote,misc

from db_validators.check_has_raw_entry_size import check_has_raw_entry_size
from db_validators.check_wasabi import check_wasabi
from db_validators.check_duplicates import check_duplicates

def do_validate( args, run ):

    if not args.no_check_raw:
        check_duplicates(args, run )
        
        check_wasabi( args, run )
        check_has_raw_entry_size( args, run )

    return True
