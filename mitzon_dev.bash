#!/bin/bash

MITAINEMITZONHOME=/opt/mitainesoft/mitzon-4.0.13dev

MITAINE_MITZON_PROC=`ps -ef | grep $MITAINEMITZONHOME/MitzonBackend/mitzonURLCmdProcessor.py | grep -v vi  | grep -v grep | awk '{print $2}'`

if [ -n "$MITAINE_MITZON_PROC" ]
then
   echo "mitzonURLCmdProcessor already running...Stopping PID='$MITAINE_MITZON_PROC'"
   kill -9 `pgrep -f  $MITAINEMITZONHOME/MitzonBackend/mitzonURLCmdProcessor.py`

else
   echo "Starting mitzon..."
fi


mkdir -p $MITAINEMITZONHOME/log

touch $MITAINEMITZONHOME/log/mitzon.log
cd $MITAINEMITZONHOME
export PYTHONUNBUFFERED=1
export PYTHONPATH=$MITAINEMITZONHOME/MitzonBackend:$MITAINEMITZONHOME:$MITAINEMITZONHOME/MitzonFrontend
export PYTHONIOENCODING=UTF-8

nohup /usr/bin/python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client $MITAINEMITZONHOME/MitzonBackend/mitzonURLCmdProcessor.py&
