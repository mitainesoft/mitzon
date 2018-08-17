#!/bin/bash
# To start garage manually. used in test context.
MITAINEGARAGEHOME=`pwd`

MITAINE_GARAGE_PROC=`ps -ef | grep garageURLCmdProcessor.py | grep -v vi  | grep -v grep | awk '{print $2}'`

if [ -n "$MITAINE_GARAGE_PROC" ]
then
   echo "garageURLCmdProcessor already running...Stopping PID='$MITAINE_GARAGE_PROC'"
   kill -9 `pgrep -f garageURLCmdProcessor.py`

else
   echo "Starting garage for test..."
fi


mkdir -p ./log

touch ./log/garage.log
cd $MITAINEGARAGEHOME 
export PYTHONUNBUFFERED=1 
export PYTHONPATH=$MITAINEGARAGEHOME/GarageBackend:$MITAINEGARAGEHOME:$MITAINEGARAGEHOME/GarageFrontend
export PYTHONIOENCODING=UTF-8

/usr/bin/python3 -u $MITAINEGARAGEHOME/GarageBackend/garageURLCmdProcessor.py



