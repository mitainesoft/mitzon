#!/bin/bash

MITAINE_MITZON_PROC=`ps -ef | grep /opt/mitainesoft/mitzon/MitzonBackend/mitzonURLCmdProcessor.py | grep -v vi  | grep -v grep | awk '{print $2}'`

if [ -n "$MITAINE_MITZON_PROC" ]
then
   echo "mitzonURLCmdProcessor already running...Stopping PID='$MITAINE_MITZON_PROC'"
   kill -9 `pgrep -f  /opt/mitainesoft/mitzon/MitzonBackend/mitzonURLCmdProcessor.py`

else
   echo "Starting mitzon..."
fi


MITAINEMITZONHOME=/opt/mitainesoft/mitzon
mkdir -p /opt/mitainesoft/mitzon/log

touch /opt/mitainesoft/mitzon/log/mitzon.log
cd $MITAINEMITZONHOME 
export PYTHONUNBUFFERED=1 
export PYTHONPATH=/opt/mitainesoft/mitzon/MitzonBackend:/opt/mitainesoft/mitzon:/opt/mitainesoft/mitzon/MitzonFrontend:/usr/local/lib/python3.7/dist-packages
export PYTHONIOENCODING=UTF-8

nohup /usr/bin/python3 -u $MITAINEMITZONHOME/MitzonBackend/mitzonURLCmdProcessor.py&

