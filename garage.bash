#!/bin/bash

kill -9 `pgrep -f  /opt/mitainesoft/garage/GarageBackend/garageURLCmdProcessor.py`

MITAINEGARAGEHOME=/opt/mitainesoft/garage
mkdir -p /opt/mitainesoft/garage/log

touch /opt/mitainesoft/garage/log/garage.log
cd $MITAINEGARAGEHOME 
export PYTHONUNBUFFERED=1 
export PYTHONPATH=/opt/mitainesoft/garage/GarageBackend:/opt/mitainesoft/garage:/opt/mitainesoft/garage/GarageFrontend
export PYTHONIOENCODING=UTF-8

nohup /usr/bin/python3 -u $MITAINEGARAGEHOME/GarageBackend/garageURLCmdProcessor.py&

