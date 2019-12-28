import logging
from MitzonBackend.GarageDoor import GarageDoor
from MitzonBackend.Valve import Valve
from MitzonBackend.ConfigManager import *
from MitzonBackend.Sensor import Sensor
from MitzonBackend.Light import Light
from MitzonBackend.CommandQResponse import *
from MitzonBackend.SingletonMeta import SingletonMeta
from time import sleep
import time
import datetime
from nanpy import ArduinoApi, SerialManager
import re

log = logging.getLogger('Garage.DeviceManager')


class DeviceManager(metaclass=SingletonMeta):
    def __init__(self):
        log.setLevel(logging.INFO)
        self.config_handler = ConfigManager()
        # self.deviceList=deviceList = {}
        self.deviceList = {}
        self.defaultgarage = self.config_handler.getConfigParam("GARAGE_MANAGER", "GARAGE_NAME_FOR_TEST")
        self.defaultValve = self.config_handler.getConfigParam("VALVE_MANAGER", "VALVE_NAME_FOR_TEST")
        self.mypin = int(self.config_handler.getConfigParam(self.defaultgarage, "GarageBoardPin"))
        self.usbConnectHandler = None
        self.serialdevicename="Any";
        self.connectUSB()

        self.createGarageObj()
        self.createValveObj()

    def createGarageObj(self):
        # replace by config
        for garageNameKey in self.config_handler.GARAGE_NAME:
            matchObj = re.findall(r'\d', garageNameKey, 1)
            garage_id = int(matchObj[0])
            logging.info(
                'Initialize board garage_id %s ** Control Board Pin %s' % (
                garageNameKey, self.config_handler.getConfigParam(self.defaultgarage, "GarageBoardPin")))
            obj = GarageDoor(garageNameKey, self.usbConnectHandler)
            objSensorProp = {}
            sensorPinArray = self.config_handler.getConfigParam(garageNameKey, "GarageSensorsBoardPin").split(",")
            sensorId = 0
            # Define Sensor objets for garage
            for sensorPinKey in sensorPinArray:
                sensor_pin_id = int(sensorPinKey)
                objSensorProp_key = "sensor_%s" % sensorId
                objSensorProp[objSensorProp_key] = Sensor(sensorId, int(sensor_pin_id))  # new object
                obj.addSensor(objSensorProp_key, objSensorProp[objSensorProp_key])
                log.debug(str(objSensorProp[objSensorProp_key]))
                sensorId += 1

            # Define Lights
            key_color=garageNameKey+'_GREEN'
            greenlightpin=int(self.config_handler.getConfigParam(garageNameKey, "GarageGreenLightBoardPin"))
            if (greenlightpin >=0):
                obj.addLight(key_color ,Light('GREEN',greenlightpin,garageNameKey,self.usbConnectHandler))
                log.info("%s light pin %d" %(key_color,greenlightpin) )
            key_color = garageNameKey + '_RED'
            redlightpin=int(self.config_handler.getConfigParam(garageNameKey, "GarageRedLightBoardPin"))
            if (redlightpin >=0):
                obj.addLight(key_color, Light('RED', redlightpin,garageNameKey,self.usbConnectHandler))
                log.info("%s light pin %d" %(key_color,redlightpin) )
            key_color = garageNameKey + '_WHITE'
            whitelightpin = int(self.config_handler.getConfigParam(garageNameKey, "GarageWhiteLightBoardPin"))
            if (whitelightpin >= 0):
                obj.addLight(key_color, Light('WHITE', whitelightpin,garageNameKey,self.usbConnectHandler))
                log.info("%s light pin %d" %(key_color,whitelightpin) )
            obj.turnOffLight('WHITE')
            obj.turnOffLight('GREEN')
            obj.turnOffLight('RED')
            obj_key = "GarageDoor_%d" % garage_id
            self.deviceList[obj_key] = obj
            garage_id = garage_id + 1

    def createValveObj(self):
        # replace by config
        for ValveNameKey in self.config_handler.VALVE_NAME:
            matchObj = re.findall(r'\d', ValveNameKey, 1)
            Valve_id = int(matchObj[0])
            logging.info(
                'Initialize board Valve_id %s ** Control Board Pin %s' % (
                    ValveNameKey, self.config_handler.getConfigParam(self.defaultValve, "BoardPin")))
            obj = Valve(ValveNameKey, self.usbConnectHandler)

            obj.turnOffLight('WHITE')
            obj.turnOffLight('GREEN')
            obj.turnOffLight('RED')
            obj_key = "ValveControl_%d" % Valve_id
            self.deviceList[obj_key] = obj
            Valve_id = Valve_id + 1

    def connectUSB(self):
        log.info("Rapberry Arduino connection Started...")
        # https://pypi.python.org/pypi/nanpy
        # https://github.com/nanpy/nanpy-firmware
        try:
            #connection = SerialManager(device='/dev/ttyUSB0')
            self.serialdevicename ==self.config_handler.getConfigParam("DEVICES", "GARAGE_SERIAL_MANAGER_DEVICE")
            tmplog = ("Garage Device configured : %s" % self.serialdevicename)
            log.info(tmplog)
            if self.serialdevicename.upper() == "ANY":
                connection = SerialManager()
            else:
                connection = SerialManager(self.serialdevicename)
            self.usbConnectHandler = ArduinoApi(connection=connection)
            tmplog="Garage Device: %s" % self.usbConnectHandler.connection.device
            log.info(tmplog)
            pass
        except Exception:
            log.info("USB Device Not found !")
            # os._exit(-1)
            return

    def testConnection(self, msg):
        self.initBoardPinMode(self.mypin)
        logbuf = "Arduino Init Pin=%d" % self.mypin
        log.info(logbuf)
        for n in range(0, self.config_handler.NBR_GARAGE - 1):
            self.mypin = self.config_handler.GARAGE_BOARD_PIN[n];
            self.usbConnectHandler.digitalWrite(self.mypin, self.usbConnectHandler.HIGH)
            log.info("ON")
            sleep(2)
            self.usbConnectHandler.digitalWrite(self.mypin, self.usbConnectHandler.LOW)
            log.info("OFF")
            sleep(2)
            n += 1

    def getConnection(self):
        return self.usbConnectHandler

    def processDeviceCommand(self, mything, myservice, myid):
        # log.info(str(self.deviceList))
        logbuf = "processDeviceCommand Received: %s/%s/%s " % (mything, myservice, myid)
        log.debug(logbuf)
        if log.isEnabledFor(logging.DEBUG):
            self.listDevices()

        obj_key = "%s_%s" % (mything, myid)
        if (obj_key in self.deviceList):
            thisdevice = self.deviceList[obj_key]
            try:
                log.debug("Calling %s class %s" % (obj_key, thisdevice.__class__.__name__))
                thingToCall = getattr(thisdevice, myservice)
            except AttributeError:
                ex_text = "Method %s doesn't exist ! nothing will happen for %s/%s/%s..." % (myservice, mything, myservice, myid)
                log.exception(ex_text)
                resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", ex_text)
                # resp = CommmandQResponse(0, ex_text)
                return resp
            resp = thingToCall()
            log.debug("processDeviceCommand Class Resp String=%s" % resp.getRspPropsToString())
            pass
        else:
            ex_text = "[DeviceManager] Invalid_Command:%s_%s_%s" % (mything, myservice, myid)
            #resp = CommmandQResponse(0, ex_text)
            resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", ex_text)
            log.error(ex_text)

        # self.listDevices(self.deviceList)
        return resp

    def listDevices(self):
        devlistidx = 0
        for key in self.deviceList:
            obj = self.deviceList[key]
            sensor_status_str = ""

            if isinstance(obj, GarageDoor):
                obj.printStatus()
            else:
                log.error("typedef %s not found!" % (obj.__class__.__name__))
            devlistidx = devlistidx + 1
        return

    def get_serialdevicename(self):
        return self.serialdevicename