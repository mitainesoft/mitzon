#!/bin/bash
# To start mitzon manually. used in test context.
MITAINEMITZONHOME=`pwd`

MITAINE_MITZON_PROC=`ps -ef | grep mitzonURLCmdProcessor.py | grep -v vi  | grep -v grep | awk '{print $2}'`

if [ -n "$MITAINE_MITZON_PROC" ]
then
   echo "mitzonURLCmdProcessor already running...Stopping PID='$MITAINE_MITZON_PROC'"
   kill -9 `pgrep -f mitzonURLCmdProcessor.py`

else
   echo "Starting mitzon for test..."
fi


mkdir -p ./log

touch ./log/mitzon.log
cd $MITAINEMITZONHOME 
export PYTHONUNBUFFERED=1 
export PYTHONPATH=$MITAINEMITZONHOME/MitzonBackend:$MITAINEMITZONHOME:$MITAINEMITZONHOME/MitzonFrontend:/usr/local/lib/python3.7/dist-packages
export PYTHONIOENCODING=UTF-8

/usr/bin/python3 -u $MITAINEMITZONHOME/MitzonBackend/mitzonURLCmdProcessor.py



