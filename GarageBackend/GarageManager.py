import logging
from GarageBackend.Constants import *
from GarageBackend.ConfigManager import *
from GarageBackend.CommandQResponse import *
from GarageBackend.GarageDoor import GarageDoor
from GarageBackend.Sensor import Sensor
from GarageBackend.DeviceManager import DeviceManager
from GarageBackend.ConfigManager import *
from GarageBackend.CommandQResponse import *
from GarageBackend.AlertManager import AlertManager
from time import sleep
import time
import datetime

log = logging.getLogger('GarageManager')

class GarageManager():

    def __init__(self):
        log.info("GarageManager Starting")
        self.config_handler = ConfigManager()
        self.alarm_magr_handler = AlertManager()
        self.GarageOpenTriggerAlarmElapsedTime = float(self.config_handler.getConfigParam("GARAGE_COMMON","GarageOpenTriggerAlarmElapsedTime"))
        self.GarageOpenTriggerCloseDoorElapsedTime = float(self.config_handler.getConfigParam("GARAGE_COMMON","GarageOpenTriggerCloseDoorElapsedTime"))

    def monitor(self):
        self.dev_manager_handler = DeviceManager()
        self.deviceList=self.dev_manager_handler.deviceList
        i=0
        while (True):
            for key in self.deviceList:
                sensor_status_str = ""
                obj = self.deviceList[key]
                if isinstance(obj, GarageDoor):
                    obj.status()
                    self.checkGaragePolicy(obj)
                    pass
                else:
                    log.info("typedef not found!")

            if log.isEnabledFor(logging.INFO):
                log.info("garageManager %06d" % (i))
                self.dev_manager_handler.listDevices()
            sleep(float(self.config_handler.getConfigParam("GARAGE_MANAGER","GARAGE_MANAGER_LOOP_TIMEOUT")))
            i=i+1
        pass

    def checkGaragePolicy(self,gd: GarageDoor ):
        try:
            if gd.g_status == G_OPEN:
                tmpstr="checkGaragePolicy time=%f otime=%f NextCmdAllowedTime=%f remain=%d sec"  % (time.time(), gd.g_open_time,gd.g_next_cmd_allowed_time, gd.g_next_cmd_allowed_time-time.time())
                log.info(tmpstr )
                if (gd.g_open_time != None): #Is there an open time stamp ?
                    if time.time() > (gd.g_open_time + self.GarageOpenTriggerCloseDoorElapsedTime ):
                        status_text = gd.g_name + " GARAGE OPEN TIME EXPIRED ALERT"
                        self.alarm_magr_handler.addAlert(CommmandQResponse(0, status_text))
                        log.error(status_text)

                        #close door !
                        if gd.g_next_cmd_allowed_time != None and time.time() > gd.g_next_cmd_allowed_time:
                            gd.triggerGarageDoor()
                    elif time.time() > (gd.g_open_time + self.GarageOpenTriggerAlarmElapsedTime ):
                        status_text = gd.g_name + " GARAGE OPEN TIME WARNING ALERT"
                        self.alarm_magr_handler.addAlert(CommmandQResponse(0, status_text))
                        log.error(status_text)
                    else:
                        pass


        except Exception:
            traceback.print_exc()
            gd.g_force_ignore_cmd=True
            status_text=gd.g_name + " CLOSE BY COMMAND DISABLED"
            self.alarm_magr_handler.addAlert(CommmandQResponse(0, status_text))
            log.error(status_text)
            os._exit(-1)

