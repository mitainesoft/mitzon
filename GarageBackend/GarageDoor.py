import logging
from GarageBackend.Constants import *
from GarageBackend.ReadBuildingConfig import *
from nanpy import ArduinoApi, SerialManager

from time import sleep
import time
import datetime

log = logging.getLogger(__name__)

class GarageDoor():

    def __init__(self,garage_id,usbConnectHandler):
        self.g_id = garage_id
        self.g_name = GARAGE_NAME[garage_id]
        self.g_board_pin_relay = GARAGE_BOARD_PIN[garage_id]
        self.g_status = G_UNKNOWN
        self.g_sensor_props = {}
        self.modified_time=int(time.time())
        #self.modified=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.usbConnectHandler=usbConnectHandler

        self.initBoardPinModeOutput(GARAGE_BOARD_PIN[garage_id])


    def isGarageOpen(self,mything,myservice,myid):
        isgarageopen= True
        return isgarageopen

    def status(self):
        log.debug("GarageDoor status called !")
        for sensor in self.g_sensor_props:
            read_status = self.usbConnectHandler.digitalRead(self.g_sensor_props[sensor].board_pin_id)
            self.g_sensor_props[sensor].status=S_SENSOR_STATUS_LIST[read_status] #0 Closed 1 open
            log.info("Sensor %s Status = %d" % (sensor,read_status) )
        pass

    def addSensor(self, key,sensor_props):
        self.g_sensor_props[key]=sensor_props
        self.initBoardPinModeInput(self.g_sensor_props[key].board_pin_id)
        # log.info("Added Sensor %s to %s" % (key, self.g_name))
        log.debug(str(sensor_props))
        pass

    def initBoardPinModeOutput(self, pin):
        log.info("Init Board Pin %d Mode Output %s" % (pin, self.g_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.OUTPUT)


    def initBoardPinModeInput(self, pin):
        #self.usbConnectHandler = ArduinoApi(connection=connection)
        #ArduinoApi()

        log.info("Init Board Pin %d Mode Input %s" % (pin, self.g_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.INPUT)
