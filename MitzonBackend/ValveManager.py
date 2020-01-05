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
        #log.setLevel(logging.INFO)
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
        self.valve_last_info_log = {} #use as heart beat !
        self.last_schedule_process_time = {} #Avoid closing the valve at every loop
        self.last_alert_closed_sev3_checkvalvepolicy = {} #Avoid closing the valve at every loop
        self.last_alert_open_sev3_checkvalvepolicy = {} #Avoid closing the valve at every loop

        self.default_language=self.config_handler.getConfigParam("NOTIFICATION_COMMON", "DEFAULT_LANGUAGE")

        self.valveconfigfilename=self.config_handler.getConfigParam("INTERNAL", "VALVE_CONFIG_DEFINITION_FILE")
        self.valvesConfigJSON = {}
        self.loadValveConfig(self.valveconfigfilename)


    def loadValveConfig(self,valveconfigfilename):
        try:
            f=open(self.valveconfigfilename)
            self.valvesConfigJSON=json.load(f)
            f.close()
            for keysv in self.valvesConfigJSON:
                self.valve_last_info_log[keysv] = time.time() + float(self.config_handler.getConfigParam("VALVE_MANAGER","VALVE_DISPLAY_OPEN_STATUS_INTERVAL"))
                self.last_schedule_process_time[keysv] = time.time() #Initial time for schedule
                self.last_alert_closed_sev3_checkvalvepolicy[keysv] = time.time() - float(
                    self.config_handler.getConfigParam("INTERNAL", "LOG_SEVERITY3_REPEAT_INTERVAL")) #Initial time for schedule
                self.last_alert_open_sev3_checkvalvepolicy[keysv] = time.time() - float(
                    self.config_handler.getConfigParam("INTERNAL",
                                                       "LOG_SEVERITY3_REPEAT_INTERVAL"))  # Initial time for schedule
        except IOError:
            log.error("Config file " + self.valveconfigfilename + " does not exist ! ")
            log.error("Exiting...")
            os._exit(-1)
        except Exception:
            traceback.print_exc()
            log.error("Exiting...")
            os._exit(-1)




    def monitor(self):
        self.dev_manager_handler = DeviceManager()
        self.deviceList=self.dev_manager_handler.deviceList
        i=0

        lastlogprint = time.time()

        while (True):

            if time.time() > (self.valve_manager_start_time+60):
                if cherrypy.engine.state == cherrypy.engine.states.STARTED:
                    if i%1000==0:
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
                if i % 5 == 0:
                    log.debug("Cherrypy Web server thread monitoring off for 1 min after ValveManager thread startup")

            for key in self.deviceList:
                sensor_status_str = ""
                obj = self.deviceList[key]
                if isinstance(obj, Valve):
                    obj.updateSensor()
                    obj.determineValveOpenClosedStatus()
                    self.ScheduleValve(obj)
                    self.checkValvePolicy(obj)
                    if log.isEnabledFor(logging.DEBUG) and i % 10000 == 0:
                        tmplog = "%s Device: %s" % (obj.get_vlv_name(), obj.get_serialdevicename())
                        log.info(tmplog)
                # else:
                #     if self.error_message_count % 1000 == 0:
                #         log.info("No Valve configured!")
                #     self.error_message_count = self.error_message_count + 1

            self.alarm_mgr_handler.processAlerts()

            if i%10000==0 or time.time() > (lastlogprint+float(self.config_handler.getConfigParam("VALVE_MANAGER","VALVE_DISPLAY_ALL_STATUS_INTERVAL"))):
                log.info("** valveManager heart beat %d **" % (i))
                lastlogprint = time.time()
                self.dev_manager_handler.listDevices()
                self.alarm_mgr_handler.status()
            sleep(float(self.config_handler.getConfigParam("VALVE_MANAGER","VALVE_MANAGER_LOOP_TIMEOUT")))
            i=i+1
        pass

    #Warpper for add alert
    def addAlertWrap(self, id, device,extratxt=""):
        self.vlv_last_alert_time = time.time()
        status_text="Wrapper request for Alert %s %s %s" %(id, device,extratxt)


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

    #Schedule valvle method
    def ScheduleValve(self,vlv: Valve ):
        logtxt = "ScheduleValve: " + vlv.vlv_name +" " + vlv.vlv_status +" "
        logtxt2 = logtxt

        now = datetime.datetime.now()
        motime = "None"

        try:
            if time.time() < (self.last_schedule_process_time[vlv.vlv_name] + 60):
                # logtxt = logtxt +"Skip Schedule"
                # log.debug(logtxt)
                return logtxt
            # else:
            #     logtxt = logtxt + "Go Schedule!"
            #     log.debug(logtxt)

            #last_alert_closed_sev3_checkvalvepolicy updated in check policy
            if time.time() > (self.last_alert_closed_sev3_checkvalvepolicy[vlv.vlv_name] + float(
                    self.config_handler.getConfigParam("INTERNAL", "LOG_SEVERITY3_REPEAT_INTERVAL"))):
                log.debug(logtxt)
            self.last_schedule_process_time[vlv.vlv_name] = time.time()

            # debug messages & events handling start

            if vlv.vlv_manual_mode == True:
                if vlv.vlv_manualopen_time != None:
                    motime=datetime.datetime.fromtimestamp(vlv.vlv_manualopen_time).strftime("%Y%m%d-%H%M%S")
                #if time.time() < (vlv.vlv_manualopen_time + 60):
                logtxt = logtxt + "Skip Scheduler. Manual Mode enabled "
                log.debug(logtxt)
                return logtxt


            logtxt2 = logtxt2 +  "Manual Force Status:%s  -  Last Manual Open Time:%s" % (vlv.auto_force_close_valve,motime ) +" - "
            if time.time() > (self.last_alert_closed_sev3_checkvalvepolicy[vlv.vlv_name] + float(
                    self.config_handler.getConfigParam("INTERNAL", "LOG_SEVERITY3_REPEAT_INTERVAL"))):
                log.debug(logtxt2)  # debug


            # if vlv.vlv_manual_mode == True and vlv.vlv_manualopen_time != None and time.time() < (vlv.vlv_manualopen_time+float(self.config_handler.getConfigParam("VALVE_COMMON", "ValveOpenManualAllowedTime"))):
            #     #logtxt2 = vlv.addAlert("VO003", vlv.vlv_name, " Manually opened")
            #     logtxt2 = logtxt2 + "Manually opened"
            #     log.debug(logtxt2)
            #     return logtxt
            # else:
            #     flag = vlv.vlv_manualopen_time != None and time.time() <  (vlv.vlv_manualopen_time + float(self.config_handler.getConfigParam("VALVE_COMMON", "ValveOpenManualAllowedTime")))
            #     flagtxt = "manual was NOT Expired"
            #
            #     if (flag):
            #         flagtxt = "manual was expired"
            #
            #     if ( vlv.vlv_manual_mode == True):
            #         logtxt = logtxt +"Manual Open/Close Auto Disabled. (" + flagtxt +") "
            #         log.debug(logtxt)
            #         return logtxt

                #vlv.vlv_manual_mode = False
            #debug messages & events handling end


            tmpstartdatetime = now.strftime("%Y%m%d") +"-"
            if vlv.auto_force_close_valve == True:
                #Skip scheduling
                logtxt = logtxt + " auto_force_close_valve enabled. Skip Scheduling."
                log.debug(logtxt)
                vlv.vlv_manual_mode = False
                self.vlv_close_time = time.time()
                vlv.triggerValve("close")
                vlv.close()
                return logtxt
        except Exception:
            vlv.addAlert("SW002", vlv.vlv_name," Error force closing")
            raise Exception("Bloc Messages & events or Auto Force Close")
            return

        try:
            if vlv.vlv_name in self.valvesConfigJSON:
                cfg_start_time = self.valvesConfigJSON[vlv.vlv_name]["TimeProperties"]["start_time"]
                cfg_duration = self.valvesConfigJSON[vlv.vlv_name]["TimeProperties"]["duration"]

                valve_enable=False

                cfg_start_time_array = cfg_start_time.split(',')
                cfg_start_time_array_len=len(cfg_start_time_array)
                cfg_duration_array = cfg_duration.split(',')
                cfg_duration_array_len = len(cfg_duration_array)
                if (cfg_start_time_array_len != cfg_duration_array_len ):
                    logtxt = logtxt + "start_time & duration array len unequal (" + str(cfg_start_time_array_len) + "/"+str(cfg_duration_array_len) +")"
                    raise Exception(logtxt)

                logtxtvalvetimetrigger = ""
                for idx in range(cfg_start_time_array_len):
                    logtxt2 = vlv.vlv_name + " #" +str(idx) +">" + "start_time:"+ cfg_start_time_array[idx] +" dur:" + cfg_duration_array[idx]
                    start_datetime_str = tmpstartdatetime +  cfg_start_time_array[idx]+ ":00"   #0s to remove ambiguity
                    # logtxt = logtxt + " start_datetime #"+str(idx)+"=" + start_datetime_str
                    start_datetime =  datetime.datetime.strptime(start_datetime_str,"%Y%m%d-%H:%M:%S")
                    end_datetime = start_datetime  + datetime.timedelta(minutes=int(cfg_duration_array[idx]))

                    start_datetime_str2=start_datetime.strftime("%Y%m%d-%Hh%Mm%Ss")
                    end_datetime_str2 = end_datetime.strftime("%Y%m%d-%Hh%Mm%Ss")

                    if (now >= start_datetime and now <= end_datetime):
                        logtxt2 = logtxt2 +" Turn VALVE_ON"
                        valve_enable = valve_enable | True
                        logtxtvalvetimetrigger = logtxtvalvetimetrigger + start_datetime.strftime("%d-%Hh%Mm") + " to " + end_datetime.strftime("%d-%Hh%Mm")
                    else:
                        logtxt2 = logtxt2 + " Turn VALVE_OFF"
                        valve_enable = valve_enable | False

                    if time.time() > (self.last_alert_closed_sev3_checkvalvepolicy[vlv.vlv_name] + float(
                            self.config_handler.getConfigParam("INTERNAL", "LOG_SEVERITY3_REPEAT_INTERVAL"))):
                        logtxt2 = logtxt2 + " [s="+start_datetime_str2 + ", e="+end_datetime_str2+"] "
                        log.debug(logtxt2)

                if (valve_enable):
                    if vlv.vlv_status != G_OPEN:
                        vlv.open()
                        logtxt = logtxt +"Open "+ logtxtvalvetimetrigger
                    else:
                        logtxt = logtxt + "Already Open " + logtxtvalvetimetrigger
                else:
                    if vlv.vlv_status != G_CLOSED:
                        vlv.close()
                        logtxt = logtxt + "Closed"
                    else:
                        logtxt = logtxt + "Already Closed"

                if time.time() > (self.last_alert_closed_sev3_checkvalvepolicy[vlv.vlv_name] + float(
                        self.config_handler.getConfigParam("INTERNAL", "LOG_SEVERITY3_REPEAT_INTERVAL"))):
                    log.debug(logtxt)

            else:
                logtxt=logtxt+" not defined in " + self.valveconfigfilename
                log.error(logtxt)
                raise Exception(logtxt)
        except Exception:
            traceback.print_exc()
            vlv.auto_force_close_valve = True
            vlv.vlv_manual_mode = False
            #self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", vlv.vlv_name)
            #self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", vlv.vlv_name)
            status_text = vlv.addAlert("SW002", vlv.vlv_name, logtxt)
            vlv.vlv_last_alert_time = time.time()
            log.error(status_text)

            #Do all to close!
            self.vlv_close_time = time.time()
            vlv.triggerValve("close")
            vlv.close()

        # Display Status at fixed interval
        if vlv.vlv_status != G_CLOSED and time.time() > self.valve_last_info_log[vlv.vlv_name]:
            # limit number of logs !
            log.info(logtxt)
            self.valve_last_info_log[vlv.vlv_name] = time.time() + float(
                self.config_handler.getConfigParam("VALVE_MANAGER", "VALVE_DISPLAY_OPEN_STATUS_INTERVAL"))



#Valve policy should take precedence over schedule in case something goes wrong
    def checkValvePolicy(self,vlv: Valve ):
        logtxt = " check Valve Policy: " + vlv.vlv_name +" "
        tmpstr =""

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


            if vlv.vlv_status == G_OPEN:  #Locked Status is LOCKOPEN ! Don't allow auto close on lock open.

                # remain_time_before_next_command_allowed = vlv.vlv_next_auto_cmd_allowed_time - time.time()


                #Unused
                # if remain_time_before_next_command_allowed > 0:
                #     tmpstr="checkValvePolicy %s open=%s Allowed Next_Manual_Cmd=%s Next_Auto_Cmd=%s --> Remain=%d sec"  % (vlv.vlv_name, \
                #                                                                                     datetime.datetime.fromtimestamp(vlv.vlv_open_time).strftime("%Y%m%d-%H%M%S"), \
                #                                                                                     datetime.datetime.fromtimestamp(vlv.vlv_next_manual_cmd_allowed_time).strftime("%Y%m%d-%H%M%S"), \
                #                                                                                     datetime.datetime.fromtimestamp(vlv.vlv_next_auto_cmd_allowed_time).strftime("%Y%m%d-%H%M%S"), \
                #                                                                                     remain_time_before_next_command_allowed)
                #     if (int(time.time())%10==0  ):
                #             log.debug(tmpstr )

                if (vlv.vlv_open_time != None): #Is there an open time stamp ?
                    if time.time() > opentimecritical:
                        logtxt = logtxt + " Open Time Critical Exceeded "
                        log.debug(logtxt)
                        # self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", vlv.vlv_name)
                        # self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", vlv.vlv_name)

                        if (time.time() > vlv.vlv_last_alert_time \
                            +  float(self.config_handler.getConfigParam("INTERNAL", "LOG_SEVERITY1_REPEAT_INTERVAL"))):
                            log.critical(logtxt)

                        self.alarm_mgr_handler.clearAlertID("VO002",vlv.vlv_name)
                        self.alarm_mgr_handler.clearAlertID("VO003", vlv.vlv_name)
                        status_text = self.addAlert("VO001", vlv.vlv_name, logtxt)
                        log.warning(status_text)
                        vlv.vlv_last_alert_time = time.time()

                        self.vlv_manual_mode = False
                        vlv.auto_force_close_valve = True
                        #disable scheduler for some time because of manual mode to false and auto close impacts

                        self.last_schedule_process_time[vlv.vlv_name] = time.time() + 90
                        vlv.close()
                    elif time.time() > opentimewarning:
                        logtxt = logtxt + " Open Time Warning Exceeded!"
                        log.debug(logtxt)
                        #self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", vlv.vlv_name)
                        #self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", vlv.vlv_name)
                        if (time.time() > vlv.vlv_last_alert_time \
                            +  float(self.config_handler.getConfigParam("INTERNAL", "LOG_SEVERITY2_REPEAT_INTERVAL"))):
                            log.warning(logtxt)
                            self.last_alert_open_sev3_checkvalvepolicy[vlv.vlv_name] = time.time()
                        status_text = self.addAlert("VO002", vlv.vlv_name)
                        vlv.vlv_last_alert_time = time.time()
                        log.critical(status_text)
                        #self.vlv_manual_mode = False
                    elif time.time() > opentimehw:
                        if time.time() > (self.last_alert_open_sev3_checkvalvepolicy[vlv.vlv_name] + float(
                                self.config_handler.getConfigParam("INTERNAL", "LOG_SEVERITY3_REPEAT_INTERVAL"))):
                            logtxt = logtxt + " open HW time expired. nothing to do. OK! "
                            log.debug(logtxt)
                            self.last_alert_open_sev3_checkvalvepolicy[vlv.vlv_name] = time.time()
                    else:
                        logtxt = logtxt + vlv.vlv_status + " " + tmpstr
                if time.time() > (self.last_alert_open_sev3_checkvalvepolicy[vlv.vlv_name] + float(
                        self.config_handler.getConfigParam("INTERNAL", "LOG_SEVERITY3_REPEAT_INTERVAL"))):
                    log.debug(logtxt)
                    self.last_alert_open_sev3_checkvalvepolicy[vlv.vlv_name] = time.time()
            if vlv.vlv_status == G_CLOSED:
                if time.time() >= (vlv.vlv_close_time + 2 * float(
                        self.config_handler.getConfigParam("NOTIFICATION_MANAGER",
                                                           "NOTIFICATION_MANAGER_LOOP_TIMEOUT"))):  # Dont clear alarm right away. give time to notification manager
                    self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", vlv.vlv_name)
                    self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", vlv.vlv_name)
                    logtxt = logtxt + " G_CLOSED clearAlertDevice VALVE_COMMAND VALVE_OPEN events"

                    if time.time() > (self.last_alert_closed_sev3_checkvalvepolicy[vlv.vlv_name]+float(self.config_handler.getConfigParam("INTERNAL", "LOG_SEVERITY3_REPEAT_INTERVAL"))): #reduce load, dont clear forever
                        log.debug(logtxt)
                        #vlv.vlv_last_alert_time = time.time()
                        self.last_alert_closed_sev3_checkvalvepolicy[vlv.vlv_name] = time.time()
        except Exception:
            traceback.print_exc()
            vlv.auto_force_close_valve=True
            status_text = vlv.addAlert("SW101", vlv.vlv_name)
            vlv.vlv_last_alert_time = time.time()
            log.error(status_text)
            self.vlv_close_time = time.time()
            vlv.triggerValve("close")
            vlv.close()
            sleep(5)
            os._exit(-1)

    def addAlert(self, id, device,extratxt=""):
        self.vlv_last_alert_time = time.time()
        status_text="request for Alert %s %s %s" %(id, device,extratxt)

        try:
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
        except Exception:
            traceback.print_exc()
            logtxt = "ValveManager AddAlert Exception:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.error(logtxt)

        return status_text