#!/bin/bash

MITAINEGARAGEHOME=/opt/mitainesoft/garage
MITAINE_GARAGE_PROC=`ps -ef | grep /opt/mitainesoft/garage/GarageBackend/garageURLCmdProcessor.py | grep -v vi  | grep -v grep | awk '{print $2}'`

if [ -n "$MITAINE_GARAGE_PROC" ]
then
   echo "garageURLCmdProcessor already running PID='$MITAINE_GARAGE_PROC'"
else
   echo "launch_dashboard.bash not running($MITAINE_GARAGE_PROC)"
   echo "Starting garage..."
   $MITAINEGARAGEHOME/garage.bash
fi

##Force a query to internet. To wake up timer. Kill previous curl !
#echo Do a https request toward internet to wake up networks...
#kill -9 `pgrep -f "curl -s -o /dev/null http://jquery.com"` 2>/dev/null
#nohup curl  -s -o /dev/null https://code.jquery.com &

