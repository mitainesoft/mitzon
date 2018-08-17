#!/bin/bash

MITAINE_GARAGE_PROC=`ps -ef | grep /opt/mitainesoft/garage/GarageBackend/garageURLCmdProcessor.py | grep -v vi  | grep -v grep | awk '{print $2}'`

if [ -n "$MITAINE_GARAGE_PROC" ]
then
   echo "garageURLCmdProcessor already running...Stopping PID='$MITAINE_GARAGE_PROC'"
   kill -9 `pgrep -f  /opt/mitainesoft/garage/GarageBackend/garageURLCmdProcessor.py`

else
   echo "Starting garage..."
fi


MITAINEGARAGEHOME=/opt/mitainesoft/garage
mkdir -p /opt/mitainesoft/garage/log

touch /opt/mitainesoft/garage/log/garage.log
cd $MITAINEGARAGEHOME 
export PYTHONUNBUFFERED=1 
export PYTHONPATH=/opt/mitainesoft/garage/GarageBackend:/opt/mitainesoft/garage:/opt/mitainesoft/garage/GarageFrontend
export PYTHONIOENCODING=UTF-8

nohup /usr/bin/python3 -u $MITAINEGARAGEHOME/GarageBackend/garageURLCmdProcessor.py&

