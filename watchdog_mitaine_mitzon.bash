#!/bin/bash

MITAINEMITZONHOME=/opt/mitainesoft/mitzon
MITAINE_MITZON_PROC=`ps -ef | grep /opt/mitainesoft/mitzon/GarageBackend/mitzonURLCmdProcessor.py | grep -v vi  | grep -v grep | awk '{print $2}'`

if [ -n "$MITAINE_MITZON_PROC" ]
then
   echo "mitzonURLCmdProcessor already running PID='$MITAINE_MITZON_PROC'"
else
   echo "launch_dashboard.bash not running($MITAINE_MITZON_PROC)"
   echo "Starting mitzon..."
   $MITAINEMITZONHOME/mitzon.bash
fi

##Force a query to internet. To wake up timer. Kill previous curl !
#echo Do a https request toward internet to wake up networks...
#kill -9 `pgrep -f "curl -s -o /dev/null http://jquery.com"` 2>/dev/null
#nohup curl  -s -o /dev/null https://code.jquery.com &

