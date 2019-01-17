

import re

class fix_malformed_filenames_2019_01:

    def isbad( basename ):
        if re.match( r'APLUWCOVISMBSONAR001[\_\-]\d{8}T\d{6}$', basename ):
            return True

        return False

    def fix( client, run, args ):

        return False
