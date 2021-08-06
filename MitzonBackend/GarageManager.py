import logging
from MitzonBackend.Constants import *
from MitzonBackend.ConfigManager import *
from MitzonBackend.CommandQResponse import *
from MitzonBackend.GarageDoor import GarageDoor
from MitzonBackend.Sensor import Sensor
from MitzonBackend.DeviceManager import DeviceManager
from MitzonBackend.ConfigManager import *
from MitzonBackend.CommandQResponse import *
from MitzonBackend.AlertManager import AlertManager
from time import sleep
import time
import datetime
import cherrypy
import os, sys, traceback

log = logging.getLogger('Garage.GarageManager')

class GarageManager():

    def __init__(self):
        #log.setLevel(logging.INFO)
        log.info("GarageManager Starting")
        self.garage_manager_start_time=time.time()
        self.config_handler = ConfigManager()
        self.alarm_mgr_handler = AlertManager()
        self.GarageOpenTriggerWarningElapsedTime = float(self.config_handler.getConfigParam("GARAGE_COMMON","GarageOpenTriggerWarningElapsedTime"))
        self.GarageOpenTriggerCloseDoorElapsedTime = float(self.config_handler.getConfigParam("GARAGE_COMMON","GarageOpenTriggerCloseDoorElapsedTime"))
        self.LightGarageOpenTriggerCloseDoorPreWarningBeforeClose = float(self.config_handler.getConfigParam("GARAGE_COMMON","LightGarageOpenTriggerCloseDoorPreWarningBeforeClose"))
        self.cherryweb_server_last_run_time = time.time()
        self.gm_add_alert_time_by_type = {}  #Key is Alert type, data is time()
        self.seconds_between_alerts=float(self.config_handler.getConfigParam("ALERT", "TimeBetweenAlerts"))
        self.g_add_alert_time_by_type = {}  #Key is Alert type, data is time()
        self.error_message_count = 0




    def monitor(self):
        self.dev_manager_handler = DeviceManager()
        self.deviceList=self.dev_manager_handler.deviceList
        i=0

        while (True):

            if time.time() > (self.garage_manager_start_time+60):
                if cherrypy.engine.state == cherrypy.engine.states.STARTED:
                    log.debug("Cherrypy Web Server Thread Running")
                    self.cherryweb_server_last_run_time = time.time()
                else:
                    log.error("Cherrypy Web Server Thread Dead")
                    if (time.time() > (self.cherryweb_server_last_run_time + 120) ):
                        log.error("Cherrypy Web server thread not running, force exit of garage processes for crontab restart !")
                        os._exit(-1)
                    elif (time.time() > (self.cherryweb_server_last_run_time + 30) ):
                        # 15sec to allow for cherry pi web server to start
                        log.error("Cherrypy Web server thread not running, sending alert SW001 !")
                        # status_text = self.alarm_mgr_handler.addAlert("SW001", "RASPBERRY_PI")
                        status_text = self.addAlert("SW001", "RASPBERRY_PI","Cherrypy Web server thread not running")
                        log.error(status_text)
            else:
                log.debug("Cherrypy Web server thread monitoring off for 1 min after GarageManager thread startup")

            for key in self.deviceList:
                sensor_status_str = ""
                obj = self.deviceList[key]
                if isinstance(obj, GarageDoor):
                    obj.updateSensor()
                    obj.determineGarageDoorOpenClosedStatus()
                    self.checkGaragePolicy(obj)
                    if log.isEnabledFor(logging.DEBUG) or i % 100000 == 0:
                        tmplog = "%s Device: %s" % (obj.get_g_name(), obj.get_serialdevicename())
                        log.info(tmplog)
                # else:
                #     if self.error_message_count % 1000 == 0:
                #         log.info("No Garage configured!")
                #     self.error_message_count = self.error_message_count + 1

            self.alarm_mgr_handler.processAlerts()

            if log.isEnabledFor(logging.DEBUG) or i%10000==0:
                log.info("** garageManager heart beat %d **" % (i))
                self.dev_manager_handler.listDevices()
                self.alarm_mgr_handler.status()
            sleep(float(self.config_handler.getConfigParam("GARAGE_MANAGER","GARAGE_MANAGER_LOOP_TIMEOUT")))
            i=i+1
        pass

    #Warpper for add alert
    def addAlert(self, id, device,extratxt=""):
        self.g_last_alert_time = time.time()
        status_text="request for Alert %s %s %s" %(id, device,extratxt)


        if (id in self.gm_add_alert_time_by_type):
            lastalerttime = self.g_add_alert_time_by_type[id]
            if ( time.time() >(lastalerttime+self.seconds_between_alerts)):
                self.gm_add_alert_time_by_type.remove(id)
                log.info("%s can now be sent again for %s!" %(id,device))
            else:
                log.debug("Skip %s" % status_text)
        else:
            self.gm_add_alert_time_by_type[id]=time.time()
            status_text = self.alarm_mgr_handler.addAlert(id, device, extratxt)
            log.warning(status_text)

        return status_text


    def checkGaragePolicy(self,gd: GarageDoor ):
        try:

            # This is how the open time threasholds are defined.  refopentime is there to ensure opentime non null value.
            # ------- <opentimewarning>----<opentimeredcritical>--<opentimefinal>----<opentimelightingstop>
            refopentime = time.time()
            if gd.g_open_time != None:
                refopentime = gd.g_open_time
            opentimefinal = refopentime + float(self.GarageOpenTriggerCloseDoorElapsedTime)
            opentimeredcritical = refopentime + opentimefinal - self.LightGarageOpenTriggerCloseDoorPreWarningBeforeClose
            opentimewarning = refopentime + float(self.GarageOpenTriggerWarningElapsedTime)



            if gd.g_status == G_OPEN:  #Locked Status is LOCKOPEN ! Don't allow auto close on lock open.

                remain_time_before_next_command_allowed = gd.g_next_auto_cmd_allowed_time - time.time()


                #datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S")
                if remain_time_before_next_command_allowed > 0:
                    tmpstr="checkGaragePolicy %s open=%s Allowed Next_Manual_Cmd=%s Next_Auto_Cmd=%s --> Remain=%d sec"  % (gd.g_name, \
                                                                                                    # datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S"),\
                                                                                                    datetime.datetime.fromtimestamp(gd.g_open_time).strftime("%Y%m%d-%H%M%S"), \
                                                                                                    datetime.datetime.fromtimestamp(gd.g_next_manual_cmd_allowed_time).strftime("%Y%m%d-%H%M%S"), \
                                                                                                    datetime.datetime.fromtimestamp(gd.g_next_auto_cmd_allowed_time).strftime("%Y%m%d-%H%M%S"), \
                                                                                                    remain_time_before_next_command_allowed)
                    if (int(time.time())%60==0  ):
                        log.info(tmpstr )
                if (gd.g_open_time != None): #Is there an open time stamp ?
                    if time.time() > opentimefinal:
                        # " GARAGE OPEN TIME EXPIRED ALERT"
                        #status_text = gd.g_name + " " + self.alarm_magr_handler.alertTable["G0001"]["text"]
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", gd.g_name," from checkGaragePolicy() G_OPEN opentimefinal")
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", gd.g_name, " from checkGaragePolicy() G_OPEN opentimefinal")
                        status_text = gd.addAlert("GO001", gd.g_name)
                        gd.g_last_alert_time = time.time()
                        log.debug(status_text)
                        #close door when timer expires!
                        if gd.g_next_auto_cmd_allowed_time != None and time.time() > gd.g_next_auto_cmd_allowed_time:
                            gd.g_next_auto_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBeforeAutoRetryCloseDoor"))

                            tmpstr = "checkGaragePolicy triggerGarageDoor %s Next Auto Cmd Allowed Time=%s --> Remain=%d sec" % (gd.g_name, \
                                                                                                           datetime.datetime.fromtimestamp(gd.g_next_auto_cmd_allowed_time).strftime("%Y%m%d-%H%M%S"), \
                                                                                                           remain_time_before_next_command_allowed)
                            log.info(tmpstr)
                            if (gd.g_auto_force_ignore_garage_open_close_cmd == False and gd.g_manual_force_lock_garage_open_close_cmd==False):
                                gd.triggerGarageDoor() # return True is No Manual Overide
                            else:
                                tmpstr = "checkGaragePolicy %s Automatic triggerGarageDoor not allowed" % (gd.g_name)
                                log.info(tmpstr)

                    elif time.time() > opentimeredcritical :
                            # and time.time() < (gd.g_open_time + self.GarageOpenTriggerCloseDoorElapsedTime) :
                        #LightGarageOpenTriggerCloseDoorPreWarningBeforeClose
                        gd.startLightFlash('RED')
                        gd.stopLightFlash('GREEN')
                        gd.stopLightFlash('WHITE')
                        gd.turnOffLight('GREEN')
                        gd.turnOffLight('WHITE')
                    elif time.time() > opentimewarning:
                        # status_text = gd.g_name + " GARAGE OPEN TIME WARNING ALERT"
                        # self.alarm_magr_handler.addAlert(CommmandQResponse(0, status_text))
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", gd.g_name," from checkGaragePolicy() G_OPEN opentimewarning")
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", gd.g_name, " from checkGaragePolicy() G_OPEN opentimewarning")
                        status_text = gd.addAlert("GO002", gd.g_name)
                        gd.g_last_alert_time = time.time()
                        log.debug(status_text)
                        gd.startLightFlash('GREEN')
                    else:
                        gd.turnOnLight('GREEN')
                        gd.turnOnLight('WHITE')
                        gd.stopLightFlash('RED')
                        gd.turnOffLight('RED')


            if (gd.g_status == G_LOCKOPEN):
                #Alert in this case every GarageLockOpenTriggerAlarmElapsedTime
                if (gd.g_lock_time!=None and time.time() > (gd.g_lock_time + float(self.config_handler.getConfigParam("GARAGE_COMMON","GarageLockOpenTriggerAlarmElapsedTime")))):
                    self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", gd.g_name, "from checkGaragePolicy() G_LOCKOPEN")
                    self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", gd.g_name," from checkGaragePolicy() G_LOCKLOPEN")
                    status_text = gd.addAlert("GLO01", gd.g_name)
                    gd.startLightFlash('WHITE')
                    gd.startLightFlash('RED')
                    gd.startLightFlash('GREEN')
                    gd.g_last_alert_time = time.time()
                    log.debug(status_text)
                    gd.g_lock_time = time.time()
                else:
                    gd.stopLightFlash('WHITE')
                    gd.stopLightFlash('RED')
                    gd.stopLightFlash('GREEN')
                    gd.turnOnLight('WHITE')
                    gd.turnOnLight('GREEN')
                    gd.turnOnLight('RED')


            if (gd.g_status.find(G_CLOSED)>=0):
                if (gd.g_close_time != None): #Is there an open time stamp ?
                    # Manage specific case for light when GarageManager was restarted, door lock but door not opened !
                    close_white_light_delay=120
                    opentimelightingstop = gd.g_close_time + close_white_light_delay
                    #Change light status during the close_white_light_delay period and a little more!
                    if time.time() <= (gd.g_close_time + (close_white_light_delay+float(self.config_handler.getConfigParam("GARAGE_COMMON","GarageDoorAssumedClosedTime"))) ):
                        log.debug("%s Turn off all lights!" % gd.g_name)
                        gd.stopLightFlash('WHITE')
                        if time.time() > opentimelightingstop:
                            gd.turnOffLight('WHITE')
                        else:
                            gd.turnOnLight('WHITE')

                        gd.turnOffLight('GREEN')
                        gd.turnOffLight('RED')

                        gd.stopLightFlash('GREEN')
                        gd.stopLightFlash('RED')

        except Exception:
            traceback.print_exc()
            gd.g_auto_force_ignore_garage_open_close_cmd=True
            # status_text=gd.g_name + " CLOSE BY COMMAND DISABLED"
            # self.alarm_magr_handler.addAlert(CommmandQResponse(0, status_text))
            self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", gd.g_name)
            self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", gd.g_name)
            status_text = gd.addAlert("GCD01", gd.g_name)
            gd.g_last_alert_time = time.time()
            log.debug(status_text)
            sleep(5)
            os._exit(-1)

    def addAlert(self, id, device,extratxt=""):
        self.g_last_alert_time = time.time()
        status_text="request for Alert %s %s %s" %(id, device,extratxt)

        if (id in self.g_add_alert_time_by_type):
            lastalerttime = self.g_add_alert_time_by_type[id]
            if ( time.time() >(lastalerttime+self.seconds_between_alerts)):
                try:
                    del self.g_add_alert_time_by_type[id]
                except KeyError:
                    pass

                log.info("%s can now be sent again for %s!" %(id,device))
            else:
                log.debug("Skip %s" % status_text)
        else:
            self.g_add_alert_time_by_type[id]=time.time()
            status_text = self.alarm_mgr_handler.addAlert(id, device, extratxt)
            log.warning(status_text)

        return status_text