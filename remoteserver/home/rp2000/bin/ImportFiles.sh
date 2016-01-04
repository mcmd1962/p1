#!/bin/bash -
# vim: set autoindent filetype=sh tabstop=3 shiftwidth=3 softtabstop=3 number textwidth=175 expandtab:
#===============================================================================
#
#          FILE:  ImportFiles.sh
#
#         USAGE:  ./ImportFiles.sh
#
#   DESCRIPTION:  Import files from RP to PG
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

   LOGFILE=/home/rp2000/log/ImportFiles-$( date '+%Y-W%U' ).log
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

function ImportFile()  {
   FILE=$1
   [[ ! -e $FILE ]]  &&  {
      sleep 10
      return
   }

   logit Processing $FILE now
   RESULT=1
   cat $FILE  |
     psql -U meteruser -1 -c     \
        "copy readings(time,meterstand,minimum_verbruik,gemiddeld_verbruik,maximum_verbruik) from STDIN 
           with delimiter ',' csv"  p1_readings   &&   RESULT=0

   if [[ $RESULT -eq 0 ]];  then
      mv $FILE $DONEDIR/
      sleep 5
   else
      logit ERROR importing file $FILE
      sleep 60
   fi

}

#===============================================================================
#   MAIN SCRIPT
#===============================================================================
# p1reading-20140915-065729.csv

TODODIR=/home/rp2000/data/todo
DONEDIR=/home/rp2000/data/done
export PGPASSWORD=password

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

      ImportFile $FILE
   done

   NOW=$( date +%s )
   INTERVAL=$(( $LASTUPDATE - $PREVUPDATE ))
   PREVUPDATE=$LASTUPDATE
   SLEEP=$(( $LASTUPDATE + $INTERVAL - $NOW + 15 ))
   [[ $SLEEP -gt $(( $INTERVAL + 90 )) ]]  &&  SLEEP=$INTERVAL
   [[ $SLEEP -lt    5                  ]]  &&  SLEEP=5
   [[ $SLEEP -gt 1400                  ]]  &&  SLEEP=1400
   logit Sleeping $SLEEP seconds now
   sleep $SLEEP

done

#===============================================================================
#   STATISTICS / CLEANUP
#===============================================================================
exit 0

