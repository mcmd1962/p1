#!/bin/bash -
# vim: set autoindent filetype=sh tabstop=3 shiftwidth=3 softtabstop=3 number textwidth=175 expandtab:
#===============================================================================
#
#          FILE:  backup-postgres.sh
#
#         USAGE:  ./backup-postgres.sh
#
#   DESCRIPTION:  rsync postgres backup
#
#        AUTHOR:  Marcel (MCMD), Marcel@
#       CREATED:  01/08/2015 09:19:07 PM CET
#  DEPENDENCIES:
#      REVISION:  ---
#
#       HISTORY:
#                 + 01/08/2015/MCMD: Creation of this script.
#===============================================================================


#===  INITIALIZATION  ==========================================================
set -o nounset                                  # treat unset variables as errors

PATH=/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin:/usr/local/sbin
declare -rx ScriptName=${0##*/}             # the name of this script
declare -rx ScriptVersion="1.0"             # the version of this script

#===============================================================================
#   MAIN SCRIPT
#===============================================================================
SERVER=vps1.connected2you.com
SSHKEY=/home/user/.ssh/id_pg_backup
REMDIR=/var/lib/pgsql/backups
LOCDIR=/home/user/data/vps-postgres

date
rsync -ai -e "ssh -i $SSHKEY -l postgres" $SERVER:$REMDIR/ $LOCDIR
if [[ $? -eq 0 ]];  then
   echo
   echo deleting old files:
   find $LOCDIR -mindepth 1 -maxdepth 1 -type f -mtime +40 -delete -print
fi

#===============================================================================
#   STATISTICS / CLEANUP
#===============================================================================
exit 0

