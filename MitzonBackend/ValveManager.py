import logging
from MitzonBackend.Constants import *
from MitzonBackend.ConfigManager import *
from MitzonBackend.CommandQResponse import *
from MitzonBackend.Valve import Valve
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

log = logging.getLogger('Valve.ValveManager')

class ValveManager():

    def __init__(self):
        log.setLevel(logging.INFO)
        log.info("ValveManager Starting")
        self.valve_manager_start_time=time.time()
        self.config_handler = ConfigManager()
        self.alarm_mgr_handler = AlertManager()

        self.ValveOpenTriggerCriticalElapsedTime = float(self.config_handler.getConfigParam("VALVE_COMMON","ValveOpenTriggerCriticalElapsedTime"))
        self.ValveOpenTriggerWarningElapsedTime = float(self.config_handler.getConfigParam("VALVE_COMMON","ValveOpenTriggerWarningElapsedTime"))
        self.ValveHardwareResponseTime = float(self.config_handler.getConfigParam("VALVE_COMMON","ValveHardwareResponseTime"))

        self.cherryweb_server_last_run_time = time.time()
        self.gm_add_alert_time_by_type = {}  #Key is Alert type, data is time()
        self.seconds_between_alerts=float(self.config_handler.getConfigParam("ALERT", "TimeBetweenAlerts"))
        self.vlv_add_alert_time_by_type = {}  #Key is Alert type, data is time()
        self.error_message_count = 0




    def monitor(self):
        self.dev_manager_handler = DeviceManager()
        self.deviceList=self.dev_manager_handler.deviceList
        i=0

        while (True):

            if time.time() > (self.valve_manager_start_time+60):
                if cherrypy.engine.state == cherrypy.engine.states.STARTED:
                    log.debug("Cherrypy Web Server Thread Running")
                    self.cherryweb_server_last_run_time = time.time()
                else:
                    log.error("Cherrypy Web Server Thread Dead")
                    if (time.time() > (self.cherryweb_server_last_run_time + 120) ):
                        log.error("Cherrypy Web server thread not running, force exit of valve processes for crontab restart !")
                        os._exit(-1)
                    elif (time.time() > (self.cherryweb_server_last_run_time + 30) ):
                        # 15sec to allow for cherry pi web server to start
                        log.error("Cherrypy Web server thread not running, sending alert SW001 !")
                        # status_text = self.alarm_mgr_handler.addAlert("SW001", "RASPBERRY_PI")
                        status_text = self.addAlert("SW001", "RASPBERRY_PI")
                        log.error(status_text)
            else:
                log.debug("Cherrypy Web server thread monitoring off for 1 min after ValveManager thread startup")

            for key in self.deviceList:
                sensor_status_str = ""
                obj = self.deviceList[key]
                if isinstance(obj, Valve):
                    obj.updateSensor()
                    obj.determineValveOpenClosedStatus()
                    self.checkValvePolicy(obj)
                    if log.isEnabledFor(logging.DEBUG) or i % 100000 == 0:
                        tmplog = "%s Device: %s" % (obj.get_vlv_name(), obj.get_serialdevicename())
                        log.info(tmplog)
                else:
                    if self.error_message_count % 1000 == 0:
                        log.info("No Valve configured!")
                    self.error_message_count = self.error_message_count + 1

            self.alarm_mgr_handler.processAlerts()

            if log.isEnabledFor(logging.DEBUG) or i%10000==0:
                log.info("** valveManager heart beat %d **" % (i))
                self.dev_manager_handler.listDevices()
                self.alarm_mgr_handler.status()
            sleep(float(self.config_handler.getConfigParam("VALVE_MANAGER","VALVE_MANAGER_LOOP_TIMEOUT")))
            i=i+1
        pass

    #Warpper for add alert
    def addAlert(self, id, device,extratxt=""):
        self.vlv_last_alert_time = time.time()
        status_text="request for Alert %s %s %s" %(id, device,extratxt)


        if (id in self.gm_add_alert_time_by_type):
            lastalerttime = self.vlv_add_alert_time_by_type[id]
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


    def checkValvePolicy(self,vlv: Valve ):
        try:

            # This is how the open time threasholds are defined.  refopentime is there to ensure opentime non null value.
            # ------- <opentimewarning>----<opentimeredcritical>--<opentimefinal>----<opentimelightingstop>
            refopentime = time.time()
            if vlv.vlv_open_time != None:
                refopentime = vlv.vlv_open_time
            opentimehw = refopentime + float(self.ValveHardwareResponseTime)
            opentimecritical = refopentime + float(self.ValveOpenTriggerCriticalElapsedTime)
            opentimewarning = refopentime  + float(self.ValveOpenTriggerWarningElapsedTime)
            event_active_time = refopentime  + float(30) #Alarm hardocoded 30 sec

            logtxt = " check Valve Policy: "+vlv.vlv_name

            if vlv.vlv_status == G_OPEN:  #Locked Status is LOCKOPEN ! Don't allow auto close on lock open.

                remain_time_before_next_command_allowed = vlv.vlv_next_auto_cmd_allowed_time - time.time()


                #datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S")
                if remain_time_before_next_command_allowed > 0:
                    tmpstr="checkValvePolicy %s open=%s Allowed Next_Manual_Cmd=%s Next_Auto_Cmd=%s --> Remain=%d sec"  % (vlv.vlv_name, \
                                                                                                    datetime.datetime.fromtimestamp(vlv.vlv_open_time).strftime("%Y%m%d-%H%M%S"), \
                                                                                                    datetime.datetime.fromtimestamp(vlv.vlv_next_manual_cmd_allowed_time).strftime("%Y%m%d-%H%M%S"), \
                                                                                                    datetime.datetime.fromtimestamp(vlv.vlv_next_auto_cmd_allowed_time).strftime("%Y%m%d-%H%M%S"), \
                                                                                                    remain_time_before_next_command_allowed)
                    if (int(time.time())%10==0  ):
                            log.info(tmpstr )

                if (vlv.vlv_open_time != None): #Is there an open time stamp ?
                    if time.time() > opentimecritical:
                        #self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", vlv.vlv_name)
                        #self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", vlv.vlv_name)
                        self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", vlv.vlv_name)
                        self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", vlv.vlv_name)
                        status_text = vlv.addAlert("VO001", vlv.vlv_name)
                        vlv.vlv_last_alert_time = time.time()
                        log.debug(status_text)
                    elif time.time() > opentimewarning:
                        self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", vlv.vlv_name)
                        self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", vlv.vlv_name)
                        status_text = vlv.addAlert("VO002", vlv.vlv_name)
                        vlv.vlv_last_alert_time = time.time()
                        log.debug(status_text)
                    elif time.time() > opentimehw:
                        self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", vlv.vlv_name)
                        self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", vlv.vlv_name)
                    else:
                        logtxt = logtxt + " " + tmpstr
                log.debug(logtxt)
            if vlv.vlv_status == G_CLOSED:
                if time.time() < event_active_time: #reduce load, dont clear forever
                    self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", vlv.vlv_name)
                    self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", vlv.vlv_name)



        except Exception:
            traceback.print_exc()
            vlv.vlv_auto_force_ignore_valve_open_close_cmd=True
            # status_text=vlv.vlv_name + " CLOSE BY COMMAND DISABLED"
            # self.alarm_magr_handler.addAlert(CommmandQResponse(0, status_text))
            self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", vlv.vlv_name)
            self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", vlv.vlv_name)
            status_text = vlv.addAlert("GCD01", vlv.vlv_name)
            vlv.vlv_last_alert_time = time.time()
            log.debug(status_text)
            sleep(5)
            os._exit(-1)

    def addAlert(self, id, device,extratxt=""):
        self.vlv_last_alert_time = time.time()
        status_text="request for Alert %s %s %s" %(id, device,extratxt)

        if (id in self.vlv_add_alert_time_by_type):
            lastalerttime = self.vlv_add_alert_time_by_type[id]
            if ( time.time() >(lastalerttime+self.seconds_between_alerts)):
                try:
                    del self.vlv_add_alert_time_by_type[id]
                except KeyError:
                    pass

                log.info("%s can now be sent again for %s!" %(id,device))
            else:
                log.debug("Skip %s" % status_text)
        else:
            self.vlv_add_alert_time_by_type[id]=time.time()
            status_text = self.alarm_mgr_handler.addAlert(id, device, extratxt)
            log.warning(status_text)

        return status_text