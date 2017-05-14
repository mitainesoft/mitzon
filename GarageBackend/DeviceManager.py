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
import re

log = logging.getLogger('DeviceManager')


class DeviceManager(metaclass=SingletonMeta):
    def __init__(self):
        self.config_handler = ConfigManager()
        # self.deviceList=deviceList = {}
        self.deviceList = {}
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

        for garageNameKey in self.config_handler.GARAGE_NAME:
            matchObj = re.findall(r'\d', garageNameKey,1)
            garage_id=int(matchObj[0])
            logging.info(
                'Initialize board garage_id %s ** Control Board Pin %s' % (garageNameKey, self.config_handler.getConfigParam(self.defaultgarage, "GarageBoardPin")))
            obj = GarageDoor(garageNameKey,self.usbConnectHandler)
            objSensorProp = {}
            sensorPinArray=self.config_handler.getConfigParam(garageNameKey, "GarageSensorsBoardPin").split(",")
            sensorId=0
            for sensorPinKey in sensorPinArray:
                sensor_pin_id=int(sensorPinKey)
                objSensorProp_key = "sensor_%s" % sensorId
                objSensorProp[objSensorProp_key] = Sensor(sensorId, int(sensor_pin_id))  # new object
                obj.addSensor(objSensorProp_key, objSensorProp[objSensorProp_key])
                log.debug(str(objSensorProp[objSensorProp_key]))
                sensorId+=1
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
                # logstr = "listDevices %d) %s-%s g_status:%s " % (obj.g_id, key, obj.g_name, obj.g_status)
                logstr = "Dev: %s/%s status:%s " % (key, obj.g_name, obj.g_status)

                for sensor in obj.g_sensor_props:
                    sensor_status_str = sensor_status_str + sensor + "=" + obj.g_sensor_props[sensor].status + " "
                if obj.g_update_time != None:
                    printut=datetime.datetime.fromtimestamp(obj.g_update_time).strftime("%Y%m%d-%H%M%S")
                else:
                    printut="None"
                if obj.g_open_time != None:
                    printot = datetime.datetime.fromtimestamp(obj.g_open_time).strftime("%Y%m%d-%H%M%S")
                else:
                    printot="None"
                if obj.g_close_time!=None:
                    printct = datetime.datetime.fromtimestamp(obj.g_close_time).strftime("%Y%m%d-%H%M%S")
                else:
                    printct="None"
                if obj.g_error_time!=None:
                    printerrt = datetime.datetime.fromtimestamp(obj.g_error_time).strftime("%Y%m%d-%H%M%S")
                else:
                    printerrt="None"
                if obj.g_last_alert_send_time!=None:
                    printlast = datetime.datetime.fromtimestamp(obj.g_last_alert_send_time).strftime("%Y%m%d-%H%M%S")
                else:
                    printlast="None"
                try:
                    logstr = logstr + sensor_status_str + " utime=" + printut+ " otime=" + printot + " ctime=" + printct + " errtime=" + printerrt+ " LastAlertTime=" + printlast
                    log.info(logstr)
                except Exception:
                    log.error ("Time Stamp print error ?!?  print to stdout ")
                    print (logstr)


            else:
                log.info("typedef not found!")
            devlistidx = devlistidx + 1
        return

