import logging
from GarageBackend.GarageDoor import GarageDoor
from GarageBackend.ReadBuildingConfig import *
from GarageBackend.sensorProperties import sensorProperties


from time import sleep

from nanpy import ArduinoApi, SerialManager

log = logging.getLogger(__name__)

class DeviceManager():
    def __init__(self,deviceList):
        self.deviceList=deviceList
        self.mypin=GARAGE_BOARD_PIN[0] #Hard coded!  remove !
        connection = SerialManager()
        self.usbConnectHandler = ArduinoApi(connection=connection)
        log.info("init deviceManager")

        # replace by config
        for garage_id in range(NBR_GARAGE):
            logging.info(
                'Initialize board garage_id %d ** Control Board Pin %d' % (garage_id, GARAGE_BOARD_PIN[garage_id]))
            self.initBoardPinMode(GARAGE_BOARD_PIN[garage_id])
            obj = GarageDoor(garage_id)
            objSensorProp = {}
            for sensor_pin_id in range(len(GARAGE_SENSORS_PIN[garage_id])):
                objSensorProp_key = "sensor_%s" % sensor_pin_id
                objSensorProp[objSensorProp_key] = sensorProperties(sensor_pin_id, GARAGE_SENSORS_PIN[garage_id][
                    sensor_pin_id])  # new object
                obj.addSensor(objSensorProp_key, objSensorProp[objSensorProp_key])
                log.info(str(objSensorProp[objSensorProp_key]))
            obj_key = "garage_%d" % garage_id
            self.deviceList[obj_key] = obj
            garage_id = garage_id + 1


    def testConnection(self,deviceList):
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

    def processDeviceCommand(self,mything,myservice,myid, deviceList):
        log.info(deviceList)
        logbuf="Cmd Received: %s/%s/%s " % (mything,myservice,myid)
        log.info ( logbuf )
        if (log.isEnabledFor(logging.INFO)): self._listDevices(deviceList)

        return 0


    def _listDevices(self, deviceList):
        devlistidx = 0
        for key in deviceList:
            obj = deviceList[key]
            if isinstance(obj, GarageDoor):
                logstr = "Garage Obj %d  %s Garage Configured -  Name: %s" % (obj.g_id, key, obj.g_name)
                log.info(logstr)
            else:
                log.info("typedef not found!")

            devlistidx = devlistidx + 1
        return 0


