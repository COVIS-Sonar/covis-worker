#!/bin/sh
#
# sftp -i ~/.ssh/covis.privkey covis@pi.ooirsn.uw.edu

rclone sync  --verbose --sftp-host pi.ooirsn.uw.edu --sftp-user covis --sftp-key-file $HOME/.ssh/covis.privkey  /auto/nas/covis/data/postprocessed/Version3.2_automatic/  :sftp:processed/Automatic_Postprocessing_Version3.2/
