import logging
from GarageBackend.Constants import *
from GarageBackend.ReadBuildingConfig import *
from GarageBackend.CommandQResponse import *
from GarageBackend.GarageDoor import GarageDoor
from GarageBackend.Sensor import Sensor


from time import sleep
import time
import datetime

log = logging.getLogger('GarageManager')

class GarageManager():

    def __init__(self):
        log.info("GarageManager Starting")


    def monitor(self,deviceList):
        self.deviceList=deviceList
        i=0
        while (True):
            log.info("garageManager %06d" % (i))

            for key in self.deviceList:
                sensor_status_str = ""
                obj = self.deviceList[key]
                if isinstance(obj, GarageDoor):
                    logstr = "Garage Obj %d  %s Garage Configured -  Name: %s " % (obj.g_id, key, obj.g_name)
                    for sensor in obj.g_sensor_props:
                        sensor_status_str = sensor_status_str + sensor + "=" + obj.g_sensor_props[sensor].status + " "
                    logstr = logstr + sensor_status_str
                    log.info(logstr)
                else:
                    log.info("typedef not found!")

            sleep(GARAGE_MANAGER_LOOP_TIMEOUT)
            i=i+1
        pass



