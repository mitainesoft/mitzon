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
import cherrypy
import os, sys, traceback

log = logging.getLogger('GarageManager')

class GarageManager():

    def __init__(self):
        log.info("GarageManager Starting")
        self.config_handler = ConfigManager()
        self.alarm_mgr_handler = AlertManager()
        self.GarageOpenTriggerAlarmElapsedTime = float(self.config_handler.getConfigParam("GARAGE_COMMON","GarageOpenTriggerAlarmElapsedTime"))
        self.GarageOpenTriggerCloseDoorElapsedTime = float(self.config_handler.getConfigParam("GARAGE_COMMON","GarageOpenTriggerCloseDoorElapsedTime"))
        self.cherryweb_server_last_run_time = time.time()

    def monitor(self):
        self.dev_manager_handler = DeviceManager()
        self.deviceList=self.dev_manager_handler.deviceList
        i=0



        while (True):
            if cherrypy.engine.state == cherrypy.engine.states.STARTED:
                log.debug("Cherrypy Web Server Thread Running")
                self.cherryweb_server_last_run_time = time.time()
            else:
                log.error("Cherrypy Web Server Thread Dead")
                if (time.time() > (self.cherryweb_server_last_run_time + 120) ):
                    log.error("Cherrypy Web server thread not running, force exit of garage processes !")
                    os._exit(-1)
                elif (time.time() > (self.cherryweb_server_last_run_time + 30) ):
                    # 15sec to allow for cherry pi web server to start
                    log.error("Cherrypy Web server thread not running, sending alert SW001 !")
                    status_text = self.alarm_mgr_handler.addAlert("SW001", "RASPBERRY_PI")
                    log.error(status_text)

            for key in self.deviceList:
                sensor_status_str = ""
                obj = self.deviceList[key]
                if isinstance(obj, GarageDoor):
                    obj.updateSensor()
                    obj.determineGarageDoorOpenClosedStatus()
                    self.checkGaragePolicy(obj)

                    # obj.g_light_list[obj.g_name + '_GREEN'].turnOnLight()
                    # sleep(1.00)
                    # obj.g_light_list[obj.g_name + '_GREEN'].turnOffLight()
                    # sleep(0.500)
                else:
                    log.info("typedef not found!")

            self.alarm_mgr_handler.processAlerts()

            if log.isEnabledFor(logging.INFO):
                log.info("** garageManager %d **" % (i))
                self.dev_manager_handler.listDevices()
                self.alarm_mgr_handler.status()
            sleep(float(self.config_handler.getConfigParam("GARAGE_MANAGER","GARAGE_MANAGER_LOOP_TIMEOUT")))
            i=i+1
        pass

    def checkGaragePolicy(self,gd: GarageDoor ):
        try:
            if gd.g_status == G_OPEN:  #Locked Status is LOCKOPEN !
                tmpstr="checkGaragePolicy time=%f otime=%f NextCmdAllowedTime=%f remain=%d sec"  % (time.time(), gd.g_open_time,gd.g_next_cmd_allowed_time, gd.g_next_cmd_allowed_time-time.time())
                log.info(tmpstr )
                if (gd.g_open_time != None): #Is there an open time stamp ?
                    if time.time() > (gd.g_open_time + self.GarageOpenTriggerCloseDoorElapsedTime ):
                        # " GARAGE OPEN TIME EXPIRED ALERT"
                        #status_text = gd.g_name + " " + self.alarm_magr_handler.alertTable["G0001"]["text"]
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", gd.g_name)
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", gd.g_name)
                        status_text = self.alarm_mgr_handler.addAlert("GO001", gd.g_name)
                        log.error(status_text)
                        #close door when timer expires!
                        if gd.g_next_cmd_allowed_time != None and time.time() > gd.g_next_cmd_allowed_time:
                            gd.triggerGarageDoor() # return True is No Manual Overide
                    elif time.time() > (gd.g_open_time + self.GarageOpenTriggerAlarmElapsedTime ):
                        # status_text = gd.g_name + " GARAGE OPEN TIME WARNING ALERT"
                        # self.alarm_magr_handler.addAlert(CommmandQResponse(0, status_text))
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", gd.g_name)
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", gd.g_name)
                        status_text = self.alarm_mgr_handler.addAlert("GO002", gd.g_name)
                        log.error(status_text)
                    else:
                        pass

            if (gd.g_status == G_LOCKOPEN):
                #Alert in this case every GarageLockOpenTriggerAlarmElapsedTime
                if (gd.g_lock_time!=None and time.time() > (gd.g_lock_time + float(self.config_handler.getConfigParam("GARAGE_COMMON","GarageLockOpenTriggerAlarmElapsedTime")))):
                    self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", gd.g_name)
                    self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", gd.g_name)
                    status_text = self.alarm_mgr_handler.addAlert("GLO01", gd.g_name)
                    log.error(status_text)


        except Exception:
            traceback.print_exc()
            gd.g_auto_force_ignore_garage_open_close_cmd=True
            # status_text=gd.g_name + " CLOSE BY COMMAND DISABLED"
            # self.alarm_magr_handler.addAlert(CommmandQResponse(0, status_text))
            self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", gd.g_name)
            self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", gd.g_name)
            status_text = self.alarm_mgr_handler.addAlert("GCD01", gd.g_name)
            log.error(status_text)
            sleep(5)
            os._exit(-1)

