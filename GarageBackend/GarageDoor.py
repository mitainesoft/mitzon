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

        matchObj = re.findall(r'\d', garage_name, 1)
        garage_id = int(matchObj[0])
        self.g_id = garage_id

        self.g_name = garage_name
        self.g_board_pin_relay = int(self.config_handler.getConfigParam(self.g_name,"GarageBoardPin"))

        self.g_status = G_UNKNOWN
        self.g_prevstatus = G_UNKNOWN
        self.g_sensor_props = {}
        self.g_update_time=None
        self.g_open_time = None
        self.g_close_time = None
        self.g_error_time = None
        self.g_last_alert_send_time = None
        self.g_last_cmd_sent_time = None
        self.g_next_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBeforeRetryCloseDoor"))


        self.g_alert_light_time = None
        self.g_force_ignore_cmd = False
        self.nbrfault=0
        self.g_statusEventList=[]

        self.usbConnectHandler=usbConnectHandler

        self.initBoardPinModeOutput(int(self.config_handler.getConfigParam(self.g_name,"GarageBoardPin")))


    def isGarageOpen(self,mything,myservice,myid):
        isgarageopen= True
        return isgarageopen


    def updateSensor(self):
        sensor_status_text=""
        self.g_update_time = time.time()
        for sensor in self.g_sensor_props:
            self.g_sensor_props[sensor].s_update_time = time.time()
            read_status = self.usbConnectHandler.digitalRead(self.g_sensor_props[sensor].board_pin_id)
            self.g_sensor_props[sensor].status=S_SENSOR_STATUS_LIST[read_status] #0=open 1=closed
            sensor_status_text = sensor_status_text + "%s/%s/%s " % (self.g_name,sensor,S_SENSOR_STATUS_LIST[read_status])
            log.debug("Sensor %s Status = %d" % (sensor,read_status) )
        resp=self.dertermineGarageDoorOpenClosedStatus()
        return resp

    def dertermineGarageDoorOpenClosedStatus(self):
        log.debug("GarageDoor dertermine Door Open Closed Status called !")
        sensorkey0="[UNKNOWN]"
        sensor_status_text=A_OK
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
                        AlertManager().clearAlert()
                        self.nbrfault=0
                else:
                    self.g_status = S_ERROR
                    logstr = " %d Garage %d Sensor %s Status = %s" % (
                        i, self.g_id, sensor, S_WARNING)

                    if (S_ERROR not in self.g_statusEventList):
                        self.g_statusEventList.append(S_ERROR)
                        #log.warning(logstr)

                    self.nbrfault=self.nbrfault+1
                    if self.nbrfault>float(self.config_handler.getConfigParam("GARAGE_MANAGER", "GARAGE_MANAGER_MAX_FAILURE")):
                        sensor_status_text = "Garage " + self.g_name + " Sensor " + A_ERROR
                        self.g_sensor_props[sensor].status=S_ERROR
                        self.g_status=G_ERROR
                        am=AlertManager()
                        am.addAlert(CommmandQResponse(0, sensor_status_text ))
                        self.g_last_alert_send_time = time.time()
                        log.error(sensor_status_text)
        log.debug(logstr)

        if (self.g_prevstatus != self.g_status):
            log.info(self.g_name + " change from " + self.g_prevstatus + " to " + self.g_status)
            self.g_prevstatus = self.g_status
            if self.g_status == G_OPEN:
                self.g_open_time = time.time()
            elif self.g_status == G_CLOSED:
                self.g_close_time = time.time()
            elif self.g_status == G_ERROR:
                self.g_error_time = time.time()
        else:
            log.info(self.g_name + " no change !")

        resp = CommmandQResponse(0, sensor_status_text )
        return (resp)

    def status(self):
        log.debug("GarageDoor status called !")
        resp = self.updateSensor()
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

    def closeGarageDoor(self):
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
            log.error("closeGarageDoor problem !")
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