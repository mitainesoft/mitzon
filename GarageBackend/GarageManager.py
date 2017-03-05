import logging
from GarageBackend.Constants import *
from GarageBackend.ReadBuildingConfig import *
from GarageBackend.CommandQResponse import *
from nanpy import ArduinoApi, SerialManager

from time import sleep
import time
import datetime

log = logging.getLogger('GarageManager')

class GarageManager():

    def __init__(self):
        log.info("Garagemanager Starting")


    def monitor(self):
        i=0
        while (True):
            log.info("garageManager %000000d" % (i))
            sleep(GARAGE_MANAGER_LOOP_TIMEOUT)
            i=i+1
        pass



