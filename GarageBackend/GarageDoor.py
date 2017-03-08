import logging
from GarageBackend.Constants import *
from GarageBackend.ReadBuildingConfig import *
from GarageBackend.CommandQResponse import *
from nanpy import ArduinoApi, SerialManager

from time import sleep
import time
import datetime

log = logging.getLogger('GarageDoor')

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
        sensor_status_text=""
        for sensor in self.g_sensor_props:
            read_status = self.usbConnectHandler.digitalRead(self.g_sensor_props[sensor].board_pin_id)
            self.g_sensor_props[sensor].status=S_SENSOR_STATUS_LIST[read_status] #0=open 1=closed
            sensor_status_text = sensor_status_text + "%s/%s/%s " % (self.g_name,sensor,S_SENSOR_STATUS_LIST[read_status])
            log.debug("Sensor %s Status = %d" % (sensor,read_status) )

        resp = CommmandQResponse(0, sensor_status_text )
        return (resp)

    def test(self):
        self.initBoardPinModeOutput(self.g_board_pin_relay)
        logbuf="Arduino Init Pin=%d" % self.g_board_pin_relay
        log.info(logbuf)
        for n in range(0, 1):
            self.usbConnectHandler.digitalWrite(self.g_board_pin_relay, self.usbConnectHandler.HIGH)
            log.info("ON")
            sleep(3)
            self.usbConnectHandler.digitalWrite(self.g_board_pin_relay, self.usbConnectHandler.LOW)
            log.info("OFF")
            sleep(2)
            n += 1

        return CommmandQResponse(0, "testRelay Done" )

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
        log.info("Init Board Pin %d Mode Input %s" % (pin, self.g_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.INPUT)
