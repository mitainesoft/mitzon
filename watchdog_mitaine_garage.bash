#!/bin/bash

MITAINEGARAGEHOME=/opt/mitainesoft/garage
MITAINE_GARAGE_PROC=`ps -ef | grep /opt/mitainesoft/garage/GarageBackend/garageURLCmdProcessor.py | grep -v vi  | grep -v grep | awk '{print $2}'`

if [ -n "$MITAINE_GARAGE_PROC" ]
then
   echo "garageURLCmdProcessor PID='$MITAINE_GARAGE_PROC'"
else
   echo "launch_dashboard.bash not running($MITAINE_GARAGE_PROC)"
   $MITAINEGARAGEHOME/garage.bash
fi

