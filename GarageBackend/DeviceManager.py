import logging
from time import sleep

from nanpy import ArduinoApi, SerialManager

log = logging.getLogger(__name__)

class DeviceManager():
    def __init__(self,pin=7):
        self.mypin=pin
        connection = SerialManager()
        self.usbConnectHandler = ArduinoApi(connection=connection)
        log.info("init deviceManager")

    def testConnection(self):
        self.initBoardPinMode(self.mypin)
        logbuf="Arduino Pin=%d" % self.mypin
        log.info(logbuf)
        for n in range(0, 1):
            self.usbConnectHandler.digitalWrite(self.mypin, self.usbConnectHandler.HIGH)
            log.info("ON")
            sleep(2)
            self.usbConnectHandler.digitalWrite(self.mypin, self.usbConnectHandler.LOW)
            log.info("OFF")
            sleep(2)
            n += 1

    def initBoardPinMode(self, pin):
        self.mypin=pin

        self.usbConnectHandler.pinMode(self.mypin, self.usbConnectHandler.OUTPUT)

    def getConnection(self):
        return self.usbConnectHandler



