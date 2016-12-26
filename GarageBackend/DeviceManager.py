import logging
from GarageBackend.GarageDoor import GarageDoor

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

    def processDeviceCommand(self,deviceList):
        log.info(deviceList)
        devlistidx=0
        for key in deviceList:
            obj=deviceList[key]
            if isinstance(obj, GarageDoor):
                logstr = "Garage Obj %d  %s   Garage Name: %s" % (obj.g_id, key, obj.g_name)
                log.info(logstr)
            else:
                log.info("typedef not found!")

            devlistidx = devlistidx + 1

        return 0





