
from covis_db import db,hosts,remote,misc

from db_validators.check_has_raw_entry_size import check_has_raw_entry_size
from db_validators.add_raw_entry_for_wasabi import add_raw_entry_for_wasabi
from db_validators.check_duplicates import check_duplicates
from db_validators.check_host_filename_at_top_level import check_host_filename_at_top_level
from db_validators.fix_raw_entries_without_extension import fix_raw_entries_without_extension

def do_validate( args, run ):

    check_duplicates(args, run )
    check_host_filename_at_top_level( args, run )

    ## Checks that involve contacting the RAW repositories
    if args.check_raw:

        add_raw_entry_for_wasabi( args, run )
        check_has_raw_entry_size( args, run )

    return True
