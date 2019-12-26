import logging
from MitzonBackend.Constants import *
from MitzonBackend.ConfigManager import *
from MitzonBackend.CommandQResponse import *
from MitzonBackend.AlertManager import AlertManager
from MitzonBackend.GarageUtil import *

from nanpy import ArduinoApi, SerialManager
from time import sleep
import time
import datetime

from time import sleep
import time
import datetime
from MitzonBackend.ConfigManager import *

log = logging.getLogger('Garage.SprinklerControl')

class SprinklerControl():

    def __init__(self,sprinkler_name,usbConnectHandler):
        log.setLevel(logging.INFO)
        self.config_handler = ConfigManager()
        self.alarm_mgr_handler = AlertManager()

        matchObj = re.findall(r'\d', sprinkler_name, 1)
        sprinkler_id = int(matchObj[0])
        self.spkl_id = sprinkler_id

        self.spkl_name = sprinkler_name
        self.spkl_board_pin_relay = int(self.config_handler.getConfigParam(self.spkl_name,"GarageBoardPin"))

        self.spkl_status = G_UNKNOWN
        self.spkl_prevstatus = G_UNKNOWN

        self.spkl_lightstatus = ""
        self.spkl_prevlightstatus = ""

        self.spkl_light_list = {}  #Dict of lights. key = color GREEN RED WHITE
        self.spkl_update_time=time.time()
        self.spkl_open_time = None
        self.spkl_close_time = None
        self.spkl_error_time = None
        self.spkl_last_alert_time = None
        self.spkl_last_cmd_sent_time = None
        self.spkl_last_cmd_trigger_time = None
        self.spkl_next_auto_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_MANAGER", "GARAGE_MANAGER_LOOP_TIMEOUT"))
        self.spkl_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_MANAGER", "GARAGE_MANAGER_LOOP_TIMEOUT"))
        self.spkl_lock_time=None

        self.seconds_between_alerts=float(self.config_handler.getConfigParam("ALERT", "TimeBetweenAlerts"))
        self.spkl_alert_light_time = None
        self.spkl_auto_force_ignore_sprinkler_open_close_cmd = False
        self.spkl_manual_force_lock_sprinkler_open_close_cmd = False
        self.spkl_add_alert_time_by_type = {}  #Key is Alert type, data is time()

        self.nbrfault=0

        self.spkl_statusEventList=[]

        self.usbConnectHandler=usbConnectHandler
        self.initBoardPinModeOutput(int(self.config_handler.getConfigParam(self.spkl_name,"GarageBoardPin")))
        tmplog = "Garage Serial Device: %s pin %d" % (self.usbConnectHandler.connection.device, int(self.config_handler.getConfigParam(self.spkl_name,"GarageBoardPin")))
        log.info(tmplog)

    def isGarageOpen(self,mything,myservice,myid):
        return self.spkl_status==G_OPEN

    def startLightFlash(self,color):
        key=self.spkl_name+"_"+color
        if (key in self.spkl_light_list):
            # log.info("Green startFlashLight started !!!")
            self.spkl_light_list[key].startFlashLight()

    def stopLightFlash(self, color):
        key = self.spkl_name + "_" + color
        if (key in self.spkl_light_list):
            # log.info("Green startFlashLight started !!!")
            self.spkl_light_list[key].stopFlashLight()

    def turnOnLight(self, color):
        key = self.spkl_name + "_" + color
        if (key in self.spkl_light_list):
            # log.info("Green startFlashLight started !!!")
            self.spkl_light_list[key].turnOnLight()

    def turnOffLight(self, color):
        key = self.spkl_name + "_" + color
        if (key in self.spkl_light_list):
            # log.info("Green startFlashLight started !!!")
            self.spkl_light_list[key].turnOffLight()

    def addAlert(self, id, device,extratxt=""):
        self.spkl_last_alert_time = time.time()
        status_text="request for Alert %s %s %s" %(id, device,extratxt)

        if (id in self.spkl_add_alert_time_by_type):
            lastalerttime = self.spkl_add_alert_time_by_type[id]
            if ( time.time() >(lastalerttime+self.seconds_between_alerts)):
                try:
                    del self.spkl_add_alert_time_by_type[id]
                except KeyError:
                    pass

                log.info("%s can now be sent again for %s!" %(id,device))
            else:
                log.debug("Skip %s" % status_text)
        else:
            self.spkl_add_alert_time_by_type[id]=time.time()
            status_text = self.alarm_mgr_handler.addAlert(id, device, extratxt)
            log.warning(status_text)

        return status_text



    def updateSensor(self):
        self.spkl_auto_force_ignore_sprinkler_open_close_cmd = True
        #sensor_status_text=self.addAlert("HW001", self.spkl_name )
        #status_text=self.addAlert("GCD01", self.spkl_name)
        status_text="OK"
        # self.tid,self.module,self.device,self.status,self.text)
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]",self.spkl_name ,S_UNKNOWN,status_text)
        # os._exit(6)
        return resp

    def lock(self):
        tmptxt=""
        if self.spkl_manual_force_lock_sprinkler_open_close_cmd==False:
            tmptxt="%s Garage Lock down requested" % (self.spkl_name)
            self.spkl_manual_force_lock_sprinkler_open_close_cmd = True
            self.spkl_lock_time=time.time()
        else:
            self.spkl_manual_force_lock_sprinkler_open_close_cmd = False
            tmptxt="%s Garage UnLock requested" % (self.spkl_name)
            # self.spkl_lock_time=None
        log.info(tmptxt)

        # resp = CommmandQResponse(time.time() * 1000000, "[DeviceManager] " + self.determineSprinklerControlOpenClosedStatus())
        # self.tid,self.module,self.device,self.status,self.text)
        mod="[DeviceManager]"
        stat="[STATUS]"
        str0 = self.determineSprinklerControlOpenClosedStatus().split(':')
        dev=str0[0]
        if str0.__len__() >1:
            stat=str0[1]
        resp = CommmandQResponse(time.time() * 1000000, mod, dev, stat,"")

        return (resp)

    def status(self):
        log.debug("SprinklerControl status called !")
        self.updateSensor()
        rsptxt=self.spkletCmdQResponseStatusStr()

        #resp = CommmandQResponse(time.time() * 1000000, "[DeviceManager] " + self.determineSprinklerControlOpenClosedStatus())
        # self.tid,self.module,self.device,self.status,self.text)
        mod="[DeviceManager]"
        stat="[STATUS]"
        str0 = self.determineSprinklerControlOpenClosedStatus().split(':')
        dev=str0[0]
        if str0.__len__() >1:
            stat=str0[1]
        resp = CommmandQResponse(time.time() * 1000000, mod, dev, stat,rsptxt)

        return (resp)

    def getCmdQResponseStatusStr(self):
        resp_json=None
        try:
            rspstr={}
            if self.spkl_open_time != None:
                rspstr[G_OPEN]=GarageUtil.getTimePrintOut(self,time.time()-self.spkl_open_time)

            else:
                rspstr[G_OPEN]=""
            if self.spkl_close_time != None and self.spkl_open_time != None:
                rspstr[G_CLOSED] = GarageUtil.getTimePrintOut(self,time.time()-self.spkl_close_time)
            else:
                rspstr[G_CLOSED]=""
            if self.spkl_error_time != None:
                rspstr[G_ERROR] = GarageUtil.getTimePrintOut(self,time.time()-self.spkl_close_time)
            else:
                rspstr[G_ERROR]="Check!"

            if self.spkl_lock_time !=None:
                rspstr[G_LOCK] = GarageUtil.getTimePrintOut(self,time.time()-self.spkl_lock_time)
            else:
                rspstr[G_LOCK] = ""

            resp_json = json.dumps(rspstr)

        except Exception:
            log.error("Bug handling of getCmdQResponseStatusStr JSON convert")
            traceback.print_exc()
            resp_json="Error!"

        return json.dumps(resp_json)

    def clear(self):
        # resp = CommmandQResponse(time.time()*1000000, "Garage alarm cleared" )
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", "Garage alarm cleared")
        return (resp)

    def addLight(self, key,lightobj):
        self.spkl_light_list[key]=lightobj
        self.initBoardPinModeOutput(self.spkl_light_list[key].board_pin_id)
        self.turnOffLight(key)
        log.debug(str(lightobj))
        pass

    def initBoardPinModeOutput(self, pin):
        log.info("Init Board Pin %d Mode Output %s" % (pin, self.spkl_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.OUTPUT)
        self.s_update_time = time.time()


    def initBoardPinModeInput(self, pin):
        log.info("Init Board Pin %d Mode Input %s" % (pin, self.spkl_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.INPUT)
        self.s_update_time=time.time()

    def open(self):
        status_text="Open"
        self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.spkl_name)
        try:
            if self.spkl_manual_force_lock_sprinkler_open_close_cmd == False:
                if (self.spkl_status  == G_CLOSED ):
                    if time.time() > self.spkl_next_manual_cmd_allowed_time:
                        # status_text+=" open. Trigger sprinkler door !"
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", self.spkl_name)
                        self.triggerSprinklerControl()
                        status_text=self.addAlert("GTO01", self.spkl_name)
                        self.spkl_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBetweenButtonManualPressed"))
                        # self.startLightFlash('GREEN')
                    else:
                        # open denied. Too early to retry!
                        status_text = self.addAlert("GTO02", self.spkl_name)

                else:
                    # open denied. current status is " + self.spkl_status
                    status_text = self.addAlert("GTO03", self.spkl_name, self.spkl_status)

            else: #Lock!
                status_text = self.addAlert("GTO04", self.spkl_name, self.spkl_status)

            self.spkl_last_cmd_trigger_time=time.time()

        except Exception:
            traceback.print_exc()
            logstr = "open() Garage %s Status = %s Fatal Exception" % (self.spkl_name, self.spkl_status)
            log.error(logstr)
            os._exit(-1)
        # resp=CommmandQResponse(0, status_text)
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", status_text)
        log.warning(status_text)
        return resp

    def close(self):
        status_text = "Close"

        try:
            if self.spkl_auto_force_ignore_sprinkler_open_close_cmd == True:
                status_text=self.spkl_name + " " +  self.alarm_mgr_handler.alertFileListJSON["GCD01"]["text"]+" "
                # log.warning(status_text)
            else:
                if (self.spkl_status == G_OPEN and self.spkl_manual_force_lock_sprinkler_open_close_cmd == False):
                    if time.time() > self.spkl_next_manual_cmd_allowed_time:
                        # close. Trigger sprinkler door !
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.spkl_name)
                        status_text = self.addAlert("GTC01", self.spkl_name)
                        self.triggerSprinklerControl()
                        self.spkl_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBetweenButtonManualPressed"))
                        # self.startLightFlash('RED')
                    else:
                        # status_text += "close denied. Too early to retry!"
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.spkl_name)
                        status_text = self.addAlert("GTC02", self.spkl_name)
                else:
                    # status_text += "close denied. current status is " + self.spkl_status
                    self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.spkl_name)
                    status_text = self.addAlert("GTC03", self.spkl_name,self.spkl_status)
            self.spkl_last_cmd_trigger_time=time.time()

        except Exception:
            traceback.print_exc()
            logstr = "close() Garage %s Status = %s Fatal Exception" % (self.spkl_name, self.spkl_status)
            log.error(logstr)
            os._exit(-1)
        # resp=CommmandQResponse(0, status_text)
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", status_text)

        log.warning(status_text)

        return resp

    '''
    return True if OK, False if problem.
    OS exit if fatal !
    '''
    def triggerSprinklerControl(self):

        #GarageManager Check Policy will not call this because status os LOCKOPEN and OPEN in this mode !
        if (self.spkl_manual_force_lock_sprinkler_open_close_cmd):
            logtxt="Trigger sprinkler Door refused because of Manual Override"
            log.error(logtxt)
            return False;

        try:
            self.usbConnectHandler.digitalWrite(self.spkl_board_pin_relay, self.usbConnectHandler.HIGH)
            log.debug(self.spkl_name + " Press button!")
            sleep(float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeToKeepButtonPressedMilliSec"))/1000)
            self.usbConnectHandler.digitalWrite(self.spkl_board_pin_relay, self.usbConnectHandler.LOW)
            log.debug(self.spkl_name + " Release button!")
            sleep(float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeToKeepButtonPressedMilliSec"))/1000)
            self.spkl_next_auto_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBeforeAutoRetryCloseDoor"))
            self.spkl_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBetweenButtonManualPressed"))
            self.spkl_last_cmd_sent_time=time.time()
            log.info("%s Open/Close door button pressed" % (self.spkl_name))
        except Exception:
            log.error("triggerSprinklerControl Open or Close button problem !")
            traceback.print_exc()
            os._exit(-1)

        return True



    def printStatus(self):
        logstr = "%s:%s " % (self.spkl_name, self.spkl_status)

        all_light_status=self.spkletAllLightStatus()

        if self.spkl_update_time != None:
            printut = datetime.datetime.fromtimestamp(self.spkl_update_time).strftime("%Y%m%d-%H%M%S")
        else:
            printut = "None"
        if self.spkl_open_time != None:
            printot = datetime.datetime.fromtimestamp(self.spkl_open_time).strftime("%Y%m%d-%H%M%S")
        else:
            printot = "None"
        if self.spkl_close_time != None:
            printct = datetime.datetime.fromtimestamp(self.spkl_close_time).strftime("%Y%m%d-%H%M%S")
        else:
            printct = "None"
        if self.spkl_error_time != None:
            printerrt = datetime.datetime.fromtimestamp(self.spkl_error_time).strftime("%Y%m%d-%H%M%S")
        else:
            printerrt = "None"
        if self.spkl_last_alert_time != None:
            printlast = datetime.datetime.fromtimestamp(self.spkl_last_alert_time).strftime("%Y%m%d-%H%M%S")
        else:
            printlast = "None"
        try:
            logstr = logstr + "updte=" + printut + " opn=" + printot + " clse=" + printct + " err=" + printerrt + " Alert=" + printlast + " Lights:" + all_light_status
            log.info(logstr)
        except Exception:
            log.error("Time Stamp print error ?!?  print to stdout ")
            print(logstr)

    def getAllLightStatus(self):
        all_light_status = ""
        for color in sorted({"GREEN", "RED", "WHITE"}):
            key_dev_color = self.spkl_name + "_" + color
            if key_dev_color in self.spkl_light_list:
                light_status = color[0]
                if self.spkl_light_list[key_dev_color].getLightStatus() == "ON":
                    all_light_status += light_status.lower()
                elif self.spkl_light_list[key_dev_color].getLightStatus() == "FLASH":
                    all_light_status += light_status.upper()
                else:
                    all_light_status += "-"
            else:
                log.debug("%s %s light defined yet" % (color,self.spkl_name))
        return all_light_status

    def test(self):
        self.initBoardPinModeOutput(self.spkl_board_pin_relay)
        logbuf = "Arduino Init Pin=%d" % self.spkl_board_pin_relay
        log.info(logbuf)
        for n in range(0, 1):
            self.usbConnectHandler.digitalWrite(self.spkl_board_pin_relay, self.usbConnectHandler.HIGH)
            log.info("ON")
            sleep(3)
            self.usbConnectHandler.digitalWrite(self.spkl_board_pin_relay, self.usbConnectHandler.LOW)
            log.info("OFF")
            sleep(2)
            n += 1
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", "test!")

        return resp

    def get_serialdevicename(self):
        return self.usbConnectHandler.connection.device

    def get_g_name(self):
        return self.spkl_name
