import logging
from GarageBackend.Constants import *
from GarageBackend.ConfigManager import *
from GarageBackend.CommandQResponse import *
from GarageBackend.GarageDoor import GarageDoor
from GarageBackend.Sensor import Sensor
from GarageBackend.DeviceManager import DeviceManager
from GarageBackend.ConfigManager import *
from time import sleep
import time
import datetime

log = logging.getLogger('GarageManager')

class GarageManager():

    def __init__(self):
        log.info("GarageManager Starting")
        self.config_handler = ConfigManager()


    def monitor(self):
        self.dev_manager_handler = DeviceManager()
        self.deviceList=self.dev_manager_handler.deviceList
        i=0
        while (True):
            if log.isEnabledFor(logging.INFO):
                log.info("garageManager %06d" % (i))
                self.dev_manager_handler.listDevices()

            for key in self.deviceList:
                sensor_status_str = ""
                obj = self.deviceList[key]
                if isinstance(obj, GarageDoor):
                    obj.status()
                    pass
                else:
                    log.info("typedef not found!")
            sleep(float(self.config_handler.getConfigParam("GARAGE_MANAGER","GARAGE_MANAGER_LOOP_TIMEOUT")))
            # sleep(self.config_handler.GARAGE_MANAGER_LOOP_TIMEOUT)
            i=i+1
        pass



