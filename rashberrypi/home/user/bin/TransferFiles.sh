#!/bin/bash -
# vim: set autoindent filetype=sh tabstop=3 shiftwidth=3 softtabstop=3 number textwidth=175 expandtab:
#===============================================================================
#
#          FILE:  TransferFiles.sh
#
#         USAGE:  ./TransferFiles.sh
#
#   DESCRIPTION:  Transfer files from RP to VPS
#
#        AUTHOR:  Marcel
#       CREATED:  09/15/2014 09:25:47 PM CEST
#  DEPENDENCIES:
#      REVISION:  ---
#
#       HISTORY:
#                 + 09/15/2014/MCMD: Creation of this script.
#===============================================================================


#===  INITIALIZATION  ==========================================================
set -o nounset                                  # treat unset variables as errors

PATH=/bin:/usr/bin:/usr/local/bin:/sbin:/usr/sbin:/usr/local/sbin
declare -rx ScriptName=${0##*/}             # the name of this script
declare -rx ScriptVersion="1.0"             # the version of this script


#===============================================================================
#   FUNCTIONS
#===============================================================================
function logit()  {

   LOGFILE=/home/user/log/TransferFiles-W$( date +%U ).log
   if [[ ${#1} -gt 0 ]];  then
      echo $( date '+%Y%m%d %H%M%S' )  -  $@  >> $LOGFILE
   else
      echo                                    >> $LOGFILE
   fi
}

function countFiles()  {
   COUNT=$( ls $TODODIR/$FILENAME  2> /dev/null  |  wc -l )
   echo $COUNT
}

function TransferFile()  {
   FILE=$1
   [[ ! -e $FILE ]]  &&  {
      sleep 10
      return
   }

   logit Processing $FILE now
   scp -i $KEYFILE $FILE  $REMOTE_USER@$REMOTE_SERVER:data/todo/
   RESULT=$?
   if [[ $RESULT -eq 0 ]];  then
      mv $FILE $DONEDIR/
      sleep 5
   else
      logit ERROR transporting file, RESULT=$RESULT
      sleep 60
   fi

}

#===============================================================================
#   MAIN SCRIPT
#===============================================================================
# p1reading-20140915-065729.csv

TODODIR=/home/user/data
DONEDIR=/home/user/data/done
KEYFILE=/home/user/.ssh/id_rp2000_vps
REMOTE_SERVER=remote.server
REMOTE_USER=remote.user

FILENAME=p1reading-20??????-??????.csv
[[ ! -d $DONEDIR ]]  &&  mkdir $DONEDIR

PREVUPDATE=$( date +%s )
PREVUPDATE=$(( $PREVUPDATE - 1000 ))

# Endless loop
while true;  do

   while [[ $( countFiles ) -eq 0 ]];  do
      sleep 15
   done

   # We should have a file to transfer here
   LASTUPDATE=0
   for FILE in $TODODIR/$FILENAME;  do
      MODFILE=$( stat -c %Y $FILE )
      [[ $MODFILE -gt $LASTUPDATE ]]  &&  LASTUPDATE=$MODFILE

      TransferFile $FILE
   done

   NOW=$( date +%s )
   INTERVAL=$(( $LASTUPDATE - $PREVUPDATE ))
   PREVUPDATE=$LASTUPDATE
   SLEEP=$(( $LASTUPDATE + $INTERVAL - $NOW + 15 ))
   [[ $SLEEP -gt $(( $INTERVAL + 90 )) ]]  &&  SLEEP=$INTERVAL
   [[ $SLEEP -lt    5                  ]]  &&  SLEEP=5
   [[ $SLEEP -gt 1500                  ]]  &&  SLEEP=1500
   logit Sleeping $SLEEP seconds now
   sleep $SLEEP

done

#===============================================================================
#   STATISTICS / CLEANUP
#===============================================================================
exit 0


