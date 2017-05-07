import logging
from GarageBackend.GarageDoor import GarageDoor
from GarageBackend.ConfigManager import *
from GarageBackend.Sensor import Sensor
from GarageBackend.CommandQResponse import *
from GarageBackend.SingletonMeta import SingletonMeta
from time import sleep
import time
import datetime
from nanpy import ArduinoApi, SerialManager

log = logging.getLogger('DeviceManager')


class DeviceManager(metaclass=SingletonMeta):
    def __init__(self):
        self.config_handler = ConfigManager()
        self.deviceList=deviceList = {}
        self.defaultgarage=self.config_handler.getConfigParam("GARAGE_MANAGER","GARAGE_NAME_FOR_TEST")
        self.mypin= int(self.config_handler.getConfigParam(self.defaultgarage, "GarageBoardPin"))
        self.usbConnectHandler = None


        log.info("Rapberry Arduino connection Started...")
        # https://pypi.python.org/pypi/nanpy
        # https://github.com/nanpy/nanpy-firmware
        try:
            connection = SerialManager()
            self.usbConnectHandler = ArduinoApi(connection=connection)
            log.info("init deviceManager")
        except Exception:
            log.info("USB Device Not found !")
            return

        # replace by config

        for garage_id in range(self.config_handler.NBR_GARAGE):
            logging.info(
                'Initialize board garage_id %d ** Control Board Pin %d' % (garage_id, self.config_handler.GARAGE_BOARD_PIN[garage_id]))
            obj = GarageDoor(garage_id,self.usbConnectHandler)
            objSensorProp = {}
            for sensor_pin_id in range(len(self.config_handler.GARAGE_SENSORS_PIN[garage_id])):
                objSensorProp_key = "sensor_%s" % sensor_pin_id
                objSensorProp[objSensorProp_key] = Sensor(sensor_pin_id, self.config_handler.GARAGE_SENSORS_PIN[garage_id][
                    sensor_pin_id])  # new object
                obj.addSensor(objSensorProp_key, objSensorProp[objSensorProp_key])
                log.info(str(objSensorProp[objSensorProp_key]))
            obj_key = "GarageDoor_%d" % garage_id
            self.deviceList[obj_key] = obj
            garage_id = garage_id + 1


    def testConnection(self,msg):
        self.initBoardPinMode(self.mypin)
        logbuf="Arduino Init Pin=%d" % self.mypin
        log.info(logbuf)
        for n in range(0, self.config_handler.NBR_GARAGE-1):
            self.mypin=self.config_handler.GARAGE_BOARD_PIN[n];
            self.usbConnectHandler.digitalWrite(self.mypin, self.usbConnectHandler.HIGH)
            log.info("ON")
            sleep(2)
            self.usbConnectHandler.digitalWrite(self.mypin, self.usbConnectHandler.LOW)
            log.info("OFF")
            sleep(2)
            n += 1



    def getConnection(self):
        return self.usbConnectHandler

    def processDeviceCommand(self,mything,myservice,myid):
        #log.info(str(self.deviceList))
        logbuf="processDeviceCommand Received: %s/%s/%s " % (mything,myservice,myid)
        log.debug ( logbuf )
        if log.isEnabledFor(logging.DEBUG):
            self.listDevices()

        obj_key = "%s_%s" % (mything,myid)
        if ( obj_key in self.deviceList):
            thisdevice = self.deviceList[obj_key]
            try:
                log.debug("Calling %s class %s" % (obj_key, thisdevice.__class__.__name__)  )
                thingToCall = getattr(thisdevice, myservice)
            except AttributeError:
                ex_text="Method %s doesn't exist ! nothing will happen for %s/%s/%s..." % (myservice,mything,myservice,myid)
                log.exception(ex_text)
                resp = CommmandQResponse(0,ex_text)
                return resp
            resp=thingToCall()
            pass
        else:
            ex_text="Invalid command %s/%s/%s"  % (mything,myservice,myid)
            resp = CommmandQResponse(0, ex_text)
            log.error(ex_text)

        #self.listDevices(self.deviceList)
        return resp

    def listDevices(self):
        devlistidx = 0
        for key in self.deviceList:
            obj = self.deviceList[key]
            sensor_status_str=""
            if isinstance(obj, GarageDoor):
                logstr = "listDevices Garage Obj#%d %s Garage Configured - Name:%s  g_status:%s " % (obj.g_id, key, obj.g_name, obj.g_status)
                for sensor in obj.g_sensor_props:
                    sensor_status_str = sensor_status_str + sensor + "=" + obj.g_sensor_props[sensor].status + " "
                printdate=datetime.datetime.fromtimestamp(obj.g_sensor_props[sensor].modified_time).strftime("%Y%m%d-%H%M%S")
                logstr = logstr + sensor_status_str + " Modified_Time=" + printdate
                log.info(logstr)
            else:
                log.info("typedef not found!")
            devlistidx = devlistidx + 1
        return

