#!/bin/sh

rclone sync  --progress --sftp-host pi.ooirsn.uw.edu --sftp-user covis --sftp-key-file $HOME/.ssh/covis.privkey  /auto/nas/covis/data/postprocessed/Version3.2_automatic/  :sftp:processed/Version3.2_automatic/
