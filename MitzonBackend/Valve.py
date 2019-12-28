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

log = logging.getLogger('Valve.Valve')

class Valve():

    def __init__(self,valve_name,usbConnectHandler):
        log.setLevel(logging.INFO)
        self.config_handler = ConfigManager()
        self.alarm_mgr_handler = AlertManager()

        matchObj = re.findall(r'\d', valve_name, 1)
        valve_id = int(matchObj[0])
        self.vlv_id = valve_id

        self.vlv_name = valve_name
        self.vlv_board_pin_relay = int(self.config_handler.getConfigParam(self.vlv_name,"OutBoardPin"))

        self.vlv_status = G_UNKNOWN
        self.vlv_prevstatus = G_UNKNOWN

        self.vlv_lightstatus = ""
        self.vlv_prevlightstatus = ""

        self.vlv_light_list = {}  #Dict of lights. key = color GREEN RED WHITE
        self.vlv_update_time=time.time()
        self.vlv_open_time = None
        self.vlv_error_time = None
        self.vlv_last_alert_time = None
        self.vlv_last_cmd_sent_time = None
        self.vlv_last_cmd_trigger_time = None
        self.vlv_next_auto_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("VALVE_MANAGER", "VALVE_MANAGER_LOOP_TIMEOUT"))
        self.vlv_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("VALVE_MANAGER", "VALVE_MANAGER_LOOP_TIMEOUT"))
        self.vlv_lock_time=None

        self.seconds_between_alerts=float(self.config_handler.getConfigParam("ALERT", "TimeBetweenAlerts"))
        self.vlv_alert_light_time = None
        self.vlv_auto_force_ignore_valve_open_close_cmd = False
        self.vlv_manual_force_lock_valve_open_close_cmd = False
        self.vlv_add_alert_time_by_type = {}  #Key is Alert type, data is time()

        self.nbrfault=0

        self.vlv_statusEventList=[]

        self.usbConnectHandler=usbConnectHandler
        self.initBoardPinModeOutput(int(self.config_handler.getConfigParam(self.vlv_name,"OutBoardPin")))
        tmplog = "Valve Serial Device: %s pin %d" % (self.usbConnectHandler.connection.device, int(self.config_handler.getConfigParam(self.vlv_name,"OutBoardPin")))
        log.info(tmplog)

        #Force close on startup
        self.vlv_close_time = time.time()
        self.triggerValve("close")

    def isValveOpen(self,mything,myservice,myid):
        return self.vlv_status==G_OPEN

    def startLightFlash(self,color):
        key=self.vlv_name+"_"+color
        if (key in self.vlv_light_list):
            # log.info("Green startFlashLight started !!!")
            self.vlv_light_list[key].startFlashLight()

    def stopLightFlash(self, color):
        key = self.vlv_name + "_" + color
        if (key in self.vlv_light_list):
            # log.info("Green startFlashLight started !!!")
            self.vlv_light_list[key].stopFlashLight()

    def turnOnLight(self, color):
        key = self.vlv_name + "_" + color
        if (key in self.vlv_light_list):
            # log.info("Green startFlashLight started !!!")
            self.vlv_light_list[key].turnOnLight()

    def turnOffLight(self, color):
        key = self.vlv_name + "_" + color
        if (key in self.vlv_light_list):
            # log.info("Green startFlashLight started !!!")
            self.vlv_light_list[key].turnOffLight()

    def addAlert(self, id, device,extratxt=""):
        self.vlv_last_alert_time = time.time()
        status_text="request for Alert %s %s %s" %(id, device,extratxt)

        if (id in self.vlv_add_alert_time_by_type):
            lastalerttime = self.vlv_add_alert_time_by_type[id]
            if ( time.time() >(lastalerttime+self.seconds_between_alerts)):
                try:
                    del self.vlv_add_alert_time_by_type[id]
                except KeyError:
                    pass

                log.info("%s can now be sent again for %s!" %(id,device))
            else:
                log.debug("Skip %s" % status_text)
        else:
            self.vlv_add_alert_time_by_type[id]=time.time()
            status_text = self.alarm_mgr_handler.addAlert(id, device, extratxt)
            log.warning(status_text)

        return status_text

    def determineValveOpenClosedStatus(self):
        log.debug("Valve Determine Status called !")
        valve_status_text=self.vlv_name+":"+self.vlv_status
        logstr=""
        do_print_status=False

        if (self.vlv_prevstatus != self.vlv_status):
            self.vlv_update_time = time.time()
            do_print_status = True

            if (self.vlv_status == G_OPEN):
                self.vlv_open_time = time.time()
            elif (self.vlv_status == G_CLOSED):
                self.vlv_close_time = time.time()
            elif (self.vlv_status == G_LOCKOPEN):
                self.vlv_lock_time = time.time()
            elif (self.vlv_status == G_LOCKCLOSED):
                self.vlv_lock_time = time.time()
            elif (self.vlv_status == G_ERROR):
                self.vlv_error_time = time.time()
            elif (self.vlv_status == G_UNKNOWN):
                self.vlv_update_time = time.time()


        self.vlv_prevstatus = self.vlv_status
        if (do_print_status == True):
            self.printStatus()
        return (valve_status_text)

    def updateSensor(self):

        #Nothing to check here ! Weather API @Todo
        try:
            status_text="OK"
            # self.tid,self.module,self.device,self.status,self.text)
        except Exception:
            self.vlv_auto_force_ignore_valve_open_close_cmd = True
            sensor_status_text = self.addAlert("HW101", self.vlv_name )
            status_text = self.addAlert("VCD01", self.vlv_name)

        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]",self.vlv_name ,self.vlv_status,status_text)

        return resp

    def lock(self):
        tmptxt=""
        if self.vlv_manual_force_lock_valve_open_close_cmd==False:
            tmptxt="%s Valve Lock down requested" % (self.vlv_name)
            self.vlv_manual_force_lock_valve_open_close_cmd = True
            self.vlv_lock_time=time.time()
        else:
            self.vlv_manual_force_lock_valve_open_close_cmd = False
            tmptxt="%s Valve UnLock requested" % (self.vlv_name)
            # self.vlv_lock_time=None
        log.info(tmptxt)

        # resp = CommmandQResponse(time.time() * 1000000, "[DeviceManager] " + self.determineValveOpenClosedStatus())
        # self.tid,self.module,self.device,self.status,self.text)
        mod="[DeviceManager]"
        stat="[STATUS]"
        str0 = self.determineValveOpenClosedStatus().split(':')
        dev=str0[0]
        if str0.__len__() >1:
            stat=str0[1]
        resp = CommmandQResponse(time.time() * 1000000, mod, dev, stat,"")

        return (resp)

    def status(self):
        log.debug("Valve status called !")
        self.updateSensor()
        rsptxt=self.getCmdQResponseStatusStr()

        #resp = CommmandQResponse(time.time() * 1000000, "[DeviceManager] " + self.determineValveOpenClosedStatus())
        # self.tid,self.module,self.device,self.status,self.text)
        mod="[DeviceManager]"
        stat="[STATUS]"
        str0 = self.determineValveOpenClosedStatus().split(':')
        dev=str0[0]
        if str0.__len__() >1:
            stat=str0[1]
        resp = CommmandQResponse(time.time() * 1000000, mod, dev, stat,rsptxt)

        return (resp)

    def getCmdQResponseStatusStr(self):
        resp_json=None
        try:
            rspstr={}
            if self.vlv_open_time != None:
                rspstr[G_OPEN]=GarageUtil.getTimePrintOut(self,time.time()-self.vlv_open_time)

            else:
                rspstr[G_OPEN]=""
            if self.vlv_close_time != None and self.vlv_open_time != None:
                rspstr[G_CLOSED] = GarageUtil.getTimePrintOut(self,time.time()-self.vlv_close_time)
            else:
                rspstr[G_CLOSED]=""
            if self.vlv_error_time != None:
                rspstr[G_ERROR] = GarageUtil.getTimePrintOut(self,time.time()-self.vlv_close_time)
            else:
                rspstr[G_ERROR]="Check!"

            if self.vlv_lock_time !=None:
                rspstr[G_LOCK] = GarageUtil.getTimePrintOut(self,time.time()-self.vlv_lock_time)
            else:
                rspstr[G_LOCK] = ""

            resp_json = json.dumps(rspstr)

        except Exception:
            log.error("Bug handling of getCmdQResponseStatusStr JSON convert")
            traceback.print_exc()
            resp_json="Error!"

        return json.dumps(resp_json)

    def clear(self):
        # resp = CommmandQResponse(time.time()*1000000, "Valve alarm cleared" )
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", "Valve alarm cleared")
        return (resp)

    def addLight(self, key,lightobj):
        self.vlv_light_list[key]=lightobj
        self.initBoardPinModeOutput(self.vlv_light_list[key].board_pin_id)
        self.turnOffLight(key)
        log.debug(str(lightobj))
        pass

    def initBoardPinModeOutput(self, pin):
        log.info("Init Board Pin %d Mode Output %s" % (pin, self.vlv_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.OUTPUT)
        self.s_update_time = time.time()


    def initBoardPinModeInput(self, pin):
        log.info("Init Board Pin %d Mode Input %s" % (pin, self.vlv_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.INPUT)
        self.s_update_time=time.time()

    def open(self):
        status_text="Open"
        self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", self.vlv_name)
        try:
            if self.vlv_manual_force_lock_valve_open_close_cmd == False:
                if (self.vlv_status  == G_CLOSED ):
                    if time.time() > self.vlv_next_manual_cmd_allowed_time:
                        # status_text+=" open. Trigger valve door !"
                        self.alarm_mgr_handler.clearAlertDevice("VALVE_OPEN", self.vlv_name)
                        self.triggerValve("open")
                        status_text=self.addAlert("VTO01", self.vlv_name)
                        self.vlv_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("VALVE_COMMON", "TimeBetweenButtonManualPressed"))
                        # self.startLightFlash('GREEN')
                    else:
                        # open denied. Too early to retry!
                        status_text = self.addAlert("VTO02", self.vlv_name)

                else:
                    # open denied. current status is " + self.vlv_status
                    status_text = self.addAlert("VTO03", self.vlv_name, self.vlv_status)

            else: #Lock!
                status_text = self.addAlert("VTO04", self.vlv_name, self.vlv_status)

            self.vlv_last_cmd_trigger_time=time.time()

        except Exception:
            traceback.print_exc()
            logstr = "open() Valve %s Status = %s Fatal Exception" % (self.vlv_name, self.vlv_status)
            log.error(logstr)
            os._exit(-1)
        # resp=CommmandQResponse(0, status_text)
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", status_text)
        log.debug(status_text)
        return resp

    def close(self):
        status_text = "Close"

        try:
            if self.vlv_auto_force_ignore_valve_open_close_cmd == True:
                status_text=self.vlv_name + " " +  self.alarm_mgr_handler.alertFileListJSON["Fr"]["GCD01"]["text"]+" "
                # log.warning(status_text)
            else:
                if (self.vlv_status == G_OPEN and self.vlv_manual_force_lock_valve_open_close_cmd == False):
                    if time.time() > self.vlv_next_manual_cmd_allowed_time:
                        # close. Trigger valve door !
                        self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", self.vlv_name)
                        status_text = self.addAlert("VTC01", self.vlv_name)
                        self.triggerValve("close")
                        self.vlv_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("VALVE_COMMON", "TimeBetweenButtonManualPressed"))
                        # self.startLightFlash('RED')
                    else:
                        # status_text += "close denied. Too early to retry!"
                        self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", self.vlv_name)
                        status_text = self.addAlert("VTC02", self.vlv_name)
                else:
                    # Refused, already closed !
                    self.alarm_mgr_handler.clearAlertDevice("VALVE_COMMAND", self.vlv_name)
                    status_text = self.addAlert("VTC03", self.vlv_name,self.vlv_status)
            self.vlv_last_cmd_trigger_time=time.time()

        except Exception:
            traceback.print_exc()
            logstr = "close() Valve %s Status = %s Fatal Exception" % (self.vlv_name, self.vlv_status)
            log.error(logstr)
            os._exit(-1)
        # resp=CommmandQResponse(0, status_text)
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", status_text)

        log.debug(status_text)

        return resp

    '''
    return True if OK, False if problem.
    OS exit if fatal !
    '''
    def triggerValve(self,cmd="close"):
        logtxt=self.vlv_name+" "+cmd+" triggerValve "
        #ValveManager Check Policy will not call this because status os LOCKOPEN and OPEN in this mode !


        try:
            if (cmd == "open"):
                self.vlv_open_time = time.time()
                if (self.vlv_manual_force_lock_valve_open_close_cmd):
                    logtxt = logtxt + "Trigger valve open refused because of Manual Override"
                else:
                    self.usbConnectHandler.digitalWrite(self.vlv_board_pin_relay, self.usbConnectHandler.HIGH)
                    self.vlv_status=G_OPEN
            elif cmd == "close":
                self.vlv_close_time = time.time()
                self.usbConnectHandler.digitalWrite(self.vlv_board_pin_relay, self.usbConnectHandler.LOW)
                self.vlv_status = G_CLOSED
            else:
                self.usbConnectHandler.digitalWrite(self.vlv_board_pin_relay, self.usbConnectHandler.LOW)
                self.vlv_status = G_ERROR
                logtxt = logtxt + "Error with triggerValve command"
                status_text = self.addAlert("SW101", self.vlv_name)

            self.vlv_next_auto_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("VALVE_COMMON", "TimeBeforeAutoRetryClose"))
            self.vlv_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("VALVE_COMMON", "TimeBetweenButtonManualPressed"))
            self.vlv_last_cmd_sent_time=time.time()
            log.debug(logtxt)

        except Exception:
            log.error("triggerValve Open or Close fatal error !")
            traceback.print_exc()
            os._exit(-1)

        return True



    def printStatus(self):
        logstr = "%s:%s " % (self.vlv_name, self.vlv_status)


        if self.vlv_update_time != None:
            printut = datetime.datetime.fromtimestamp(self.vlv_update_time).strftime("%Y%m%d-%H%M%S")
        else:
            printut = "None"
        if self.vlv_open_time != None:
            printot = datetime.datetime.fromtimestamp(self.vlv_open_time).strftime("%Y%m%d-%H%M%S")
        else:
            printot = "None"
        if self.vlv_close_time != None:
            printct = datetime.datetime.fromtimestamp(self.vlv_close_time).strftime("%Y%m%d-%H%M%S")
        else:
            printct = "None"
        if self.vlv_error_time != None:
            printerrt = datetime.datetime.fromtimestamp(self.vlv_error_time).strftime("%Y%m%d-%H%M%S")
        else:
            printerrt = "None"
        if self.vlv_last_alert_time != None:
            printlast = datetime.datetime.fromtimestamp(self.vlv_last_alert_time).strftime("%Y%m%d-%H%M%S")
        else:
            printlast = "None"
        try:
            logstr = logstr + "updte=" + printut + " opn=" + printot + " clse=" + printct + " err=" + printerrt + " Alert=" + printlast
            log.info(logstr)
        except Exception:
            log.error("Time Stamp print error ?!?  print to stdout ")
            print(logstr)

    def getAllLightStatus(self):
        all_light_status = ""
        for color in sorted({"GREEN", "RED", "WHITE"}):
            key_dev_color = self.vlv_name + "_" + color
            if key_dev_color in self.vlv_light_list:
                light_status = color[0]
                if self.vlv_light_list[key_dev_color].getLightStatus() == "ON":
                    all_light_status += light_status.lower()
                elif self.vlv_light_list[key_dev_color].getLightStatus() == "FLASH":
                    all_light_status += light_status.upper()
                else:
                    all_light_status += "-"
            else:
                log.debug("%s %s light defined yet" % (color,self.vlv_name))
        return all_light_status

    def test(self):
        self.initBoardPinModeOutput(self.vlv_board_pin_relay)
        logbuf = "Arduino Init Pin=%d" % self.vlv_board_pin_relay
        log.info(logbuf)
        for n in range(0, 1):
            self.usbConnectHandler.digitalWrite(self.vlv_board_pin_relay, self.usbConnectHandler.HIGH)
            log.info("ON")
            sleep(3)
            self.usbConnectHandler.digitalWrite(self.vlv_board_pin_relay, self.usbConnectHandler.LOW)
            log.info("OFF")
            sleep(2)
            n += 1
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", "test!")

        return resp

    def get_serialdevicename(self):
        return self.usbConnectHandler.connection.device

    def get_vlv_name(self):
        return self.vlv_name
