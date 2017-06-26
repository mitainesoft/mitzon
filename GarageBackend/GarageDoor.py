import logging
from GarageBackend.Constants import *
from GarageBackend.ConfigManager import *
from GarageBackend.CommandQResponse import *
from GarageBackend.AlertManager import AlertManager
from nanpy import ArduinoApi, SerialManager
from time import sleep
import time
import datetime

from time import sleep
import time
import datetime
from GarageBackend.ConfigManager import *

log = logging.getLogger('GarageDoor')

class GarageDoor():

    def __init__(self,garage_name,usbConnectHandler):
        self.config_handler = ConfigManager()
        self.alarm_mgr_handler = AlertManager()

        matchObj = re.findall(r'\d', garage_name, 1)
        garage_id = int(matchObj[0])
        self.g_id = garage_id

        self.g_name = garage_name
        self.g_board_pin_relay = int(self.config_handler.getConfigParam(self.g_name,"GarageBoardPin"))

        self.g_status = G_UNKNOWN
        self.g_prevstatus = G_UNKNOWN
        self.g_sensor_props = {}
        self.g_update_time=time.time()
        self.g_open_time = None
        self.g_close_time = None
        self.g_error_time = None
        self.g_sensor_error_time = None
        self.g_last_alert_send_time = None
        self.g_last_cmd_sent_time = None
        self.g_last_cmd_trigger_time = None
        self.g_next_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBeforeRetryCloseDoor"))


        self.g_alert_light_time = None
        self.g_auto_force_ignore_garage_open_close_cmd = False
        self.nbrfault=0

        self.g_statusEventList=[]

        self.usbConnectHandler=usbConnectHandler

        self.initBoardPinModeOutput(int(self.config_handler.getConfigParam(self.g_name,"GarageBoardPin")))


    def isGarageOpen(self,mything,myservice,myid):
        return self.g_status==G_OPEN


    def updateSensor(self):
        sensor_status_text=""
        try:
            for sensor in self.g_sensor_props:
                self.g_sensor_props[sensor].s_update_time = time.time()
                read_status = self.usbConnectHandler.digitalRead(self.g_sensor_props[sensor].board_pin_id)
                self.g_sensor_props[sensor].status=S_SENSOR_STATUS_LIST[read_status] #0=open 1=closed
                sensor_status_text = sensor_status_text + "%s/%s/%s " % (self.g_name,sensor,S_SENSOR_STATUS_LIST[read_status])
                log.debug("Sensor %s Status = %d" % (sensor,read_status) )
            resp=self.determineGarageDoorOpenClosedStatus()
        except Exception:
            self.g_last_alert_send_time = time.time()
            sensor_status_text = self.alarm_mgr_handler.addAlert("HW001", self.g_name + "_" + sensor)
            log.error(sensor_status_text)
            self.g_auto_force_ignore_garage_open_close_cmd = True
            status_text = self.alarm_mgr_handler.addAlert("GCD01", self.g_name)
            log.error(status_text)
            resp = CommmandQResponse(time.time(), status_text)

            # os._exit(6)
        return resp

    def determineGarageDoorOpenClosedStatus(self):
        log.debug("GarageDoor dertermine Door Open Closed Status called !")
        sensorkey0="[UNKNOWN]"
        sensor_status_text=self.g_name+":"+G_UNKNOWN
        logstr=""
        for i, sensor in enumerate(self.g_sensor_props):
            logstr="%d Garage %d Sensor %s Status = %s" % (i, self.g_id, sensor, self.g_sensor_props[sensor].status)

            if i==0:
                #keep track of 1st sensor, not necerraly in order to see all are the same
                sensorkey0=sensor
            else:
                if (self.g_sensor_props[sensor].status == self.g_sensor_props[sensorkey0].status):
                    self.g_status=self.g_sensor_props[sensor].status
                    if (S_ERROR in self.g_statusEventList):
                        self.g_statusEventList.remove(S_ERROR)
                        for sensorkey in self.g_sensor_props:
                            sensordevname = self.g_name + "_" + sensorkey
                            self.alarm_mgr_handler.clearAlertDevice("SENSOR", sensordevname)
                        self.nbrfault=0
                        self.g_sensor_error_time=None
                else:
                    self.g_sensor_props[sensor].status = S_ERROR
                    self.g_sensor_props[sensor].s_update_time = time.time()
                    logstr = " %d Garage %d Sensor %s Status = %s" % (
                        i, self.g_id, sensor, S_WARNING)

                    if (S_ERROR not in self.g_statusEventList):
                        self.g_statusEventList.append(S_ERROR)
                        self.g_sensor_error_time=time.time()
                        #log.warning(logstr)

                    self.nbrfault=self.nbrfault+1
                    # if self.nbrfault>float(self.config_handler.getConfigParam("GARAGE_MANAGER", "SENSOR_DEFECT_ASSESSMENT_TIME")):
                    if self.g_sensor_error_time != None and \
                                time.time() > (self.g_sensor_error_time + (float(self.config_handler.getConfigParam("GARAGE_MANAGER", "SENSOR_DEFECT_ASSESSMENT_TIME")))):
                        # sensor_status_text = "Garage " + self.g_name + " Sensor " + S_ERROR
                        self.g_sensor_props[sensor].status=S_ERROR
                        self.g_status=G_ERROR
                        # self.alarm_mgr_handler.addAlert(CommmandQResponse(0, sensor_status_text ))
                        self.g_last_alert_send_time = time.time()
                        sensor_status_text = self.alarm_mgr_handler.addAlert("GS001", self.g_name+"_"+sensor)
                        # sensor_status_text = self.alarm_mgr_handler.addAlert("GS001", self.g_name)
                        log.debug(sensor_status_text)
                        self.g_auto_force_ignore_garage_open_close_cmd = True
                        status_text = self.alarm_mgr_handler.addAlert("GCD01", self.g_name)
                        log.info(status_text)
        log.debug(logstr)

        if (self.g_prevstatus != self.g_status):
            self.g_update_time = time.time()
            sensor_status_text=self.g_name + ":" +self.g_status
            log_status_text=self.g_name + " change from " + self.g_prevstatus + " to " + self.g_status
            log.info(log_status_text)

            self.g_prevstatus = self.g_status
            if self.g_status == G_OPEN:
                self.g_open_time = time.time()
            elif self.g_status == G_CLOSED:
                # self.g_auto_force_ignore_garage_open_close_cmd = False

                self.g_close_time = time.time()
                # Clear all alarms when all sensors are OK since garage is closed.
                self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", self.g_name)
                for sensorkey in self.g_sensor_props:
                    sensordevname=self.g_name+"_"+sensorkey
                    self.alarm_mgr_handler.clearAlertDevice("SENSOR",sensordevname)

            elif self.g_status == G_ERROR:
                self.g_error_time = time.time()
        else:
            log.debug(self.g_name + "status no change !")
            if (self.g_status == G_CLOSED and self.g_error_time!=None \
                        and self.g_auto_force_ignore_garage_open_close_cmd==True \
                        and (time.time() > (self.g_error_time + float(self.config_handler.getConfigParam("GARAGE_COMMON", "GarageDoorAssumedClosedTime") ) ) )
                             ):
                if (time.time() > (self.g_close_time + float(self.config_handler.getConfigParam("GARAGE_COMMON", "GarageDoorAssumedClosedTime")))):
                    self.g_auto_force_ignore_garage_open_close_cmd = False
                    self.alarm_mgr_handler.clearAlertID("GCD01", self.g_name)
                    log.info(self.g_name+ " assumed closed. Garage back to auto close mode!")
            else:
                sensor_status_text = self.g_name + ":" + self.g_status
                # log.info(sensor_status_text)
            if self.g_update_time != None and self.g_last_cmd_sent_time != None and self.g_last_cmd_trigger_time !=None \
                and time.time() > (self.g_last_cmd_sent_time + float(self.config_handler.getConfigParam("GARAGE_COMMON", "GarageElapsedTimeForStatusChange")))\
                and self.g_last_cmd_trigger_time > (self.g_update_time+float(self.config_handler.getConfigParam("GARAGE_COMMON", "GarageElapsedTimeForStatusChange"))):
                status_text = self.alarm_mgr_handler.addAlert("HW002", self.g_name)
                self.g_update_time=time.time()
                self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
                log.info("HW problem ? :"+status_text)
            if (self.g_status == G_OPEN and self.g_open_time!=None and time.time() > (self.g_open_time+15)):
                self.alarm_mgr_handler.clearAlertID("GTO01",self.g_name)
            if (self.g_status == G_CLOSED and self.g_close_time!=None and time.time() > (self.g_close_time+15)):
                self.alarm_mgr_handler.clearAlertID("GTC01",self.g_name)



        # resp = CommmandQResponse(time.time()*1000000, sensor_status_text )
        return (sensor_status_text)

    def status(self):
        log.debug("GarageDoor status called !")
        self.updateSensor()

        resp = CommmandQResponse(time.time() * 1000000, "[DeviceManager] "+self.determineGarageDoorOpenClosedStatus())
        return (resp)

    def clear(self):
        # self.alarm_mgr_handler.clearAllAlert()
        resp = CommmandQResponse(time.time()*1000000, "Garage alarm cleared" )
        return (resp)

    def addSensor(self, key,sensor_props):
        self.g_sensor_props[key]=sensor_props
        self.initBoardPinModeInput(self.g_sensor_props[key].board_pin_id)
        log.debug(str(sensor_props))
        self.s_update_time = time.time()
        pass

    def initBoardPinModeOutput(self, pin):
        log.info("Init Board Pin %d Mode Output %s" % (pin, self.g_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.OUTPUT)
        self.s_update_time = time.time()


    def initBoardPinModeInput(self, pin):
        log.info("Init Board Pin %d Mode Input %s" % (pin, self.g_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.INPUT)
        self.s_update_time=time.time()

    def open(self):
        status_text=""
        self.g_last_cmd_trigger_time=time.time()
        if (self.g_status  == G_CLOSED):
            if time.time() > self.g_next_cmd_allowed_time:
                # status_text+=" open. Trigger garage door !"
                self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
                self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", self.g_name)
                self.triggerGarageDoor()
                status_text = self.alarm_mgr_handler.addAlert("GTO01", self.g_name)
            else:
                # status_text+="open denied. Too early to retry!"
                self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
                status_text = self.alarm_mgr_handler.addAlert("GTO02", self.g_name)

        else:
            # status_text += "open denied. current status is " + self.g_status
            self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
            status_text = self.alarm_mgr_handler.addAlert("GTO003", self.g_name,self.g_status)

        resp=CommmandQResponse(0, status_text)

        log.warning(status_text)
        return resp

    def close(self):
        self.g_last_cmd_trigger_time=time.time()
        status_text = ""
        if self.g_auto_force_ignore_garage_open_close_cmd == True:
            status_text=self.g_name + " " +  self.alarm_mgr_handler.alertFileListJSON["GDC01"]["text"]+" "
            log.warning(status_text)
        else:
            if (self.g_status == G_OPEN):
                if time.time() > self.g_next_cmd_allowed_time:
                    # status_text += " close. Trigger garage door !"
                    self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
                    status_text = self.alarm_mgr_handler.addAlert("GTC01", self.g_name)
                    self.triggerGarageDoor()
                else:
                    # status_text += "close denied. Too early to retry!"
                    self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
                    status_text = self.alarm_mgr_handler.addAlert("GTC02", self.g_name)
            else:
                # status_text += "close denied. current status is " + self.g_status
                self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
                status_text = self.alarm_mgr_handler.addAlert("GTC03", self.g_name,self.g_status)

        resp=CommmandQResponse(0, status_text)
        return resp

    def triggerGarageDoor(self):

        try:
            self.usbConnectHandler.digitalWrite(self.g_board_pin_relay, self.usbConnectHandler.HIGH)
            log.info(self.g_name + "Press button!")
            sleep(float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeToKeepButtonPressedMilliSec"))/1000)
            self.usbConnectHandler.digitalWrite(self.g_board_pin_relay, self.usbConnectHandler.LOW)
            log.info(self.g_name + "Release button!")
            sleep(float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeToKeepButtonPressedMilliSec"))/1000)
            self.g_next_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBeforeRetryCloseDoor"))
            self.g_last_cmd_sent_time=time.time()
        except Exception:
            log.error("triggerGarageDoor Open or Close problem !")
            traceback.print_exc()
            os._exit(-1)

    def test(self):
        self.initBoardPinModeOutput(self.g_board_pin_relay)
        logbuf = "Arduino Init Pin=%d" % self.g_board_pin_relay
        log.info(logbuf)
        for n in range(0, 1):
            self.usbConnectHandler.digitalWrite(self.g_board_pin_relay, self.usbConnectHandler.HIGH)
            log.info("ON")
            sleep(3)
            self.usbConnectHandler.digitalWrite(self.g_board_pin_relay, self.usbConnectHandler.LOW)
            log.info("OFF")
            sleep(2)
            n += 1

        return CommmandQResponse(0, "testRelay Done")