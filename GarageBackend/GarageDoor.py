import logging
from GarageBackend.Constants import *
from GarageBackend.ConfigManager import *
from GarageBackend.CommandQResponse import *
from GarageBackend.AlertManager import AlertManager
from nanpy import ArduinoApi, SerialManager
from time import sleep
import time
import datetime

from time import sleep
import time
import datetime
from GarageBackend.ConfigManager import *

log = logging.getLogger('Garage.GarageDoor')

class GarageDoor():

    def __init__(self,garage_name,usbConnectHandler):
        self.config_handler = ConfigManager()
        self.alarm_mgr_handler = AlertManager()

        matchObj = re.findall(r'\d', garage_name, 1)
        garage_id = int(matchObj[0])
        self.g_id = garage_id

        self.g_name = garage_name
        self.g_board_pin_relay = int(self.config_handler.getConfigParam(self.g_name,"GarageBoardPin"))

        self.g_status = G_UNKNOWN
        self.g_prevstatus = G_UNKNOWN

        self.g_lightstatus = ""
        self.g_prevlightstatus = ""

        self.g_sensor_props = {}
        self.g_light_list = {}  #Dict of lights. key = color GREEN RED WHITE
        self.g_update_time=time.time()
        self.g_open_time = None
        self.g_close_time = None
        self.g_error_time = None
        self.g_sensor_error_time = None
        self.g_last_alert_time = None
        self.g_last_cmd_sent_time = None
        self.g_last_cmd_trigger_time = None
        self.g_next_auto_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_MANAGER", "GARAGE_MANAGER_LOOP_TIMEOUT"))
        self.g_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_MANAGER", "GARAGE_MANAGER_LOOP_TIMEOUT"))
        self.g_lock_time=None

        self.seconds_between_alerts=float(self.config_handler.getConfigParam("ALERT", "TimeBetweenAlerts"))
        self.g_alert_light_time = None
        self.g_auto_force_ignore_garage_open_close_cmd = False
        self.g_manual_force_lock_garage_open_close_cmd = False
        self.g_add_alert_time_by_type = {}  #Key is Alert type, data is time()

        self.nbrfault=0

        self.g_statusEventList=[]

        self.usbConnectHandler=usbConnectHandler

        self.initBoardPinModeOutput(int(self.config_handler.getConfigParam(self.g_name,"GarageBoardPin")))


    def isGarageOpen(self,mything,myservice,myid):
        return self.g_status==G_OPEN

    def startLightFlash(self,color):
        key=self.g_name+"_"+color
        if (key in self.g_light_list):
            # log.info("Green startFlashLight started !!!")
            self.g_light_list[key].startFlashLight()

    def stopLightFlash(self, color):
        key = self.g_name + "_" + color
        if (key in self.g_light_list):
            # log.info("Green startFlashLight started !!!")
            self.g_light_list[key].stopFlashLight()

    def turnOnLight(self, color):
        key = self.g_name + "_" + color
        if (key in self.g_light_list):
            # log.info("Green startFlashLight started !!!")
            self.g_light_list[key].turnOnLight()

    def turnOffLight(self, color):
        key = self.g_name + "_" + color
        if (key in self.g_light_list):
            # log.info("Green startFlashLight started !!!")
            self.g_light_list[key].turnOffLight()

    def addAlert(self, id, device,extratxt=""):
        self.g_last_alert_time = time.time()
        status_text="request for Alert %s %s %s" %(id, device,extratxt)

        if (id in self.g_add_alert_time_by_type):
            lastalerttime = self.g_add_alert_time_by_type[id]
            if ( time.time() >(lastalerttime+self.seconds_between_alerts)):
                try:
                    del self.g_add_alert_time_by_type[id]
                except KeyError:
                    pass

                log.info("%s can now be sent again for %s!" %(id,device))
            else:
                log.debug("Skip %s" % status_text)
        else:
            self.g_add_alert_time_by_type[id]=time.time()
            status_text = self.alarm_mgr_handler.addAlert(id, device, extratxt)
            log.warning(status_text)

        return status_text



    def updateSensor(self):
        sensor_status_text=""
        try:
            for sensor in self.g_sensor_props:
                self.g_sensor_props[sensor].s_update_time = time.time()
                read_status = self.usbConnectHandler.digitalRead(self.g_sensor_props[sensor].board_pin_id)
                self.g_sensor_props[sensor].status=S_SENSOR_STATUS_LIST[read_status] #0=open 1=closed
                sensor_status_text = sensor_status_text + "%s/%s/%s " % (self.g_name,sensor,S_SENSOR_STATUS_LIST[read_status])
                log.debug("Sensor %s Status = %d" % (sensor,read_status) )
            resp=self.determineGarageDoorOpenClosedStatus()
        except Exception:
            self.g_auto_force_ignore_garage_open_close_cmd = True
            sensor_status_text=self.addAlert("HW001", self.g_name + "_" + sensor)
            status_text=self.addAlert("GCD01", self.g_name)
            # self.tid,self.module,self.device,self.status,self.text)
            resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]",self.g_name + "_" + sensor,S_ERROR,status_text)
            # os._exit(6)
        return resp

    def determineGarageDoorOpenClosedStatus(self):
        log.debug("GarageDoor dertermine Door Open Closed Status called !")
        sensorkey0="[UNKNOWN]"
        sensor_status_text=self.g_name+":"+G_UNKNOWN
        logstr=""
        do_print_status=False

        ''' Check garage status. Garage status g_status value based on sensor value if all sensors report the same'''
        for i, sensor in enumerate(self.g_sensor_props):
            logstr="%d Garage %d Sensor %s Status = %s" % (i, self.g_id, sensor, self.g_sensor_props[sensor].status)

            if i==0:
                #keep track of 1st sensor, not necessarely in order to see all are the same
                sensorkey0=sensor
            else:
                if (self.g_sensor_props[sensor].status == self.g_sensor_props[sensorkey0].status):
                    self.g_status=self.g_sensor_props[sensor].status
                    if (S_ERROR in self.g_statusEventList):
                        self.g_statusEventList.remove(S_ERROR)
                        # self.stopLightFlash('RED')
                        # self.stopLightFlash('WHITE')
                        # self.stopLightFlash('GREEN')
                        for sensorkey in self.g_sensor_props:
                            sensordevname = self.g_name + "_" + sensorkey
                            self.alarm_mgr_handler.clearAlertDevice("SENSOR", sensordevname)
                        self.nbrfault=0
                        self.g_sensor_error_time=None
                else:
                    self.g_sensor_props[sensor].status = S_ERROR
                    self.g_sensor_props[sensor].s_update_time = time.time()
                    logstr = " %d Garage %d Sensor %s Status = %s" % (
                        i, self.g_id, sensor, S_WARNING)

                    if (S_ERROR not in self.g_statusEventList):
                        self.g_statusEventList.append(S_ERROR)
                        self.g_sensor_error_time=time.time()
                        #log.warning(logstr)

                    self.nbrfault=self.nbrfault+1
                    # if self.nbrfault>float(self.config_handler.getConfigParam("GARAGE_MANAGER", "SENSOR_DEFECT_ASSESSMENT_TIME")):
                    if self.g_sensor_error_time != None and \
                                time.time() > (self.g_sensor_error_time + (float(self.config_handler.getConfigParam("GARAGE_MANAGER", "SENSOR_DEFECT_ASSESSMENT_TIME")))):
                        # sensor_status_text = "Garage " + self.g_name + " Sensor " + S_ERROR
                        self.g_sensor_props[sensor].status=S_ERROR
                        self.g_status=G_ERROR
                        sensor_status_text =self.addAlert("GS001", self.g_name+"_"+sensor)
                        self.g_auto_force_ignore_garage_open_close_cmd = True
                        status_text =self.addAlert("GCD01", self.g_name)
                        self.startLightFlash('RED')
                        self.startLightFlash('GREEN')
                        self.startLightFlash('WHITE')

        #Overide Garage but keep Sensor status upto date
        if self.g_manual_force_lock_garage_open_close_cmd == True:
            #Strip LOCK in case already there
            self.g_status=self.g_status.replace(G_LOCK,"")
            self.g_status=G_LOCK+self.g_status
            logstr = "Garage %s Status = %s" % (self.g_id, self.g_status )

            if self.g_lock_time != None and time.time() > self.g_lock_time+ float(self.config_handler.getConfigParam("ALERT", "AlertDefaultClearInterval")):
                self.alarm_mgr_handler.clearAlertID("GTO04", self.g_name)

        log.debug(logstr)

        if (self.g_prevstatus != self.g_status):
            self.g_update_time = time.time()
            sensor_status_text=self.g_name + ":" +self.g_status
            log_status_text=self.g_name + " change from " + self.g_prevstatus + " to " + self.g_status
            log.info(log_status_text)

            self.g_prevstatus = self.g_status
            if self.g_status == G_OPEN:
                self.g_open_time = time.time()
            elif self.g_status == G_CLOSED or self.g_status == G_LOCKCLOSED:
                # self.g_auto_force_ignore_garage_open_close_cmd = False
                self.g_close_time = time.time()
                # Clear all alarms when all sensors are OK since garage is closed.
                self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", self.g_name)
                self.alarm_mgr_handler.clearAlertID("GLO01", self.g_name)
                self.alarm_mgr_handler.clearAlertID("HW002", self.g_name)
                for sensorkey in self.g_sensor_props:
                    sensordevname=self.g_name+"_"+sensorkey
                    self.alarm_mgr_handler.clearAlertDevice("SENSOR",sensordevname)
            elif self.g_status == G_ERROR:
                tmpstrerr=self.g_name + ":" + self.g_status+" ERROR status"
                log.info(tmpstrerr)
                self.g_error_time = time.time()
                # self.startLightFlash('RED')
            #self.printStatus()
            do_print_status=True
        else:
            # Status no change
            # In case of previous garage error state and if garage is currently closed
            # --> Check if garage is closed and auto close was disabled
            # --> Check if enough time has passed to see if auto close can be re-enabled
            log.debug(self.g_name + "status no change !")
            if (self.g_status.find(G_CLOSED)>=0 and self.g_error_time!=None \
                        and self.g_auto_force_ignore_garage_open_close_cmd==True \
                        and (time.time() > (self.g_error_time + float(self.config_handler.getConfigParam("GARAGE_COMMON", "GarageDoorAssumedClosedTime") ) ) )
                             ):
                if (time.time() > (self.g_close_time + float(self.config_handler.getConfigParam("GARAGE_COMMON", "GarageDoorAssumedClosedTime")))):
                    self.g_auto_force_ignore_garage_open_close_cmd = False
                    self.alarm_mgr_handler.clearAlertID("GCD01", self.g_name)
                    log.info(self.g_name+ " assumed closed. Garage back to auto close mode!")
            else:
                #here the status is set when the status didnt change
                sensor_status_text = self.g_name + ":" + self.g_status
                # log.info(sensor_status_text)

            # Send HW error
            # --> if current time is greater then last command sent time + some time
            # --> and if last command trigger time is greater then last update status change + some time
            # --> and garage is not manually locked
            if self.g_update_time != None and self.g_last_cmd_sent_time != None and self.g_last_cmd_trigger_time !=None \
                and self.g_manual_force_lock_garage_open_close_cmd == False \
                and time.time() > (self.g_last_cmd_sent_time + float(self.config_handler.getConfigParam("GARAGE_COMMON", "GarageElapsedTimeForStatusChange")))\
                and self.g_last_cmd_trigger_time > (self.g_update_time+float(self.config_handler.getConfigParam("GARAGE_COMMON", "GarageElapsedTimeForStatusChange"))):
                self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
                status_text=self.addAlert("HW002", self.g_name)
                self.g_update_time=time.time()
            if (self.g_status == G_OPEN and self.g_open_time!=None and time.time() > (self.g_open_time+15)):
                self.alarm_mgr_handler.clearAlertID("GTO01",self.g_name)
            if (self.g_status.find(G_CLOSED)>=0 and self.g_close_time!=None and time.time() > (self.g_close_time+15)):
                self.alarm_mgr_handler.clearAlertID("GTC01",self.g_name)

        #Trigger a print status on light changes
        self.g_lightstatus=self.getAllLightStatus()
        if self.g_lightstatus != self.g_prevlightstatus:
            do_print_status=True
            self.g_prevlightstatus=self.g_lightstatus

        if (do_print_status == True):
            self.printStatus()
        return (sensor_status_text)

    def lock(self):
        tmptxt=""
        if self.g_manual_force_lock_garage_open_close_cmd==False:
            tmptxt="%s Garage Lock down requested" % (self.g_name)
            self.g_manual_force_lock_garage_open_close_cmd = True
            self.g_lock_time=time.time()
        else:
            self.g_manual_force_lock_garage_open_close_cmd = False
            tmptxt="%s Garage UnLock requested" % (self.g_name)
            # self.g_lock_time=None
        log.info(tmptxt)

        # resp = CommmandQResponse(time.time() * 1000000, "[DeviceManager] " + self.determineGarageDoorOpenClosedStatus())
        # self.tid,self.module,self.device,self.status,self.text)
        mod="[DeviceManager]"
        stat="[STATUS]"
        str0 = self.determineGarageDoorOpenClosedStatus().split(':')
        dev=str0[0]
        if str0.__len__() >1:
            stat=str0[1]
        resp = CommmandQResponse(time.time() * 1000000, mod, dev, stat,"")

        return (resp)

    def status(self):
        log.debug("GarageDoor status called !")
        self.updateSensor()
        rsptxt=self.getCmdQResponseStatusStr()

        #resp = CommmandQResponse(time.time() * 1000000, "[DeviceManager] " + self.determineGarageDoorOpenClosedStatus())
        # self.tid,self.module,self.device,self.status,self.text)
        mod="[DeviceManager]"
        stat="[STATUS]"
        str0 = self.determineGarageDoorOpenClosedStatus().split(':')
        dev=str0[0]
        if str0.__len__() >1:
            stat=str0[1]
        resp = CommmandQResponse(time.time() * 1000000, mod, dev, stat,rsptxt)

        return (resp)

    def getCmdQResponseStatusStr(self):
        resp_json=None
        try:
            rspstr={}
            i=0

            if self.g_open_time != None:
                rspstr[G_OPEN]=time.strftime("%Hh%M", time.localtime(self.g_open_time))
            else:
                rspstr[G_OPEN]="---"
            i+=1
            if self.g_close_time != None:
                rspstr[G_CLOSED] = time.strftime("%Hh%M", time.localtime(self.g_close_time))
            else:
                rspstr[G_CLOSED]="----"
            i += 1
            if self.g_error_time != None:
                rspstr[G_ERROR] = time.strftime("%Hh%M", time.localtime(self.g_close_time))
            else:
                rspstr[G_ERROR]="-----"
            i += 1

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

    def addSensor(self, key,sensor_props):
        self.g_sensor_props[key]=sensor_props
        self.initBoardPinModeInput(self.g_sensor_props[key].board_pin_id)
        log.debug(str(sensor_props))
        self.s_update_time = time.time()
        pass

    def addLight(self, key,lightobj):
        self.g_light_list[key]=lightobj
        self.initBoardPinModeOutput(self.g_light_list[key].board_pin_id)
        self.turnOffLight(key)
        log.debug(str(lightobj))
        pass

    def initBoardPinModeOutput(self, pin):
        log.info("Init Board Pin %d Mode Output %s" % (pin, self.g_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.OUTPUT)
        self.s_update_time = time.time()


    def initBoardPinModeInput(self, pin):
        log.info("Init Board Pin %d Mode Input %s" % (pin, self.g_name))
        self.usbConnectHandler.pinMode(pin, self.usbConnectHandler.INPUT)
        self.s_update_time=time.time()

    def open(self):
        status_text="Open"
        self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
        try:
            if self.g_manual_force_lock_garage_open_close_cmd == False:
                if (self.g_status  == G_CLOSED ):
                    if time.time() > self.g_next_manual_cmd_allowed_time:
                        # status_text+=" open. Trigger garage door !"
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_OPEN", self.g_name)
                        self.triggerGarageDoor()
                        status_text=self.addAlert("GTO01", self.g_name)
                        self.g_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBetweenButtonManualPressed"))
                        # self.startLightFlash('GREEN')
                    else:
                        # open denied. Too early to retry!
                        status_text = self.addAlert("GTO02", self.g_name)

                else:
                    # open denied. current status is " + self.g_status
                    status_text = self.addAlert("GTO03", self.g_name, self.g_status)

            else: #Lock!
                status_text = self.addAlert("GTO04", self.g_name, self.g_status)

            self.g_last_cmd_trigger_time=time.time()

        except Exception:
            traceback.print_exc()
            logstr = "open() Garage %s Status = %s Fatal Exception" % (self.g_name, self.g_status)
            log.error(logstr)
            os._exit(-1)
        # resp=CommmandQResponse(0, status_text)
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", status_text)
        log.warning(status_text)
        return resp

    def close(self):
        status_text = "Close"

        try:
            if self.g_auto_force_ignore_garage_open_close_cmd == True:
                status_text=self.g_name + " " +  self.alarm_mgr_handler.alertFileListJSON["GCD01"]["text"]+" "
                # log.warning(status_text)
            else:
                if (self.g_status == G_OPEN and self.g_manual_force_lock_garage_open_close_cmd == False):
                    if time.time() > self.g_next_manual_cmd_allowed_time:
                        # close. Trigger garage door !
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
                        status_text = self.addAlert("GTC01", self.g_name)
                        self.triggerGarageDoor()
                        self.g_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBetweenButtonManualPressed"))
                        # self.startLightFlash('RED')
                    else:
                        # status_text += "close denied. Too early to retry!"
                        self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
                        status_text = self.addAlert("GTC02", self.g_name)
                else:
                    # status_text += "close denied. current status is " + self.g_status
                    self.alarm_mgr_handler.clearAlertDevice("GARAGE_COMMAND", self.g_name)
                    status_text = self.addAlert("GTC03", self.g_name,self.g_status)
            self.g_last_cmd_trigger_time=time.time()

        except Exception:
            traceback.print_exc()
            logstr = "close() Garage %s Status = %s Fatal Exception" % (self.g_name, self.g_status)
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
    def triggerGarageDoor(self):

        #GarageManager Check Policy will not call this because status os LOCKOPEN and OPEN in this mode !
        if (self.g_manual_force_lock_garage_open_close_cmd):
            logtxt="Trigger garage Door refused because of Manual Override"
            log.error(logtxt)
            return False;

        try:
            self.usbConnectHandler.digitalWrite(self.g_board_pin_relay, self.usbConnectHandler.HIGH)
            log.debug(self.g_name + " Press button!")
            sleep(float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeToKeepButtonPressedMilliSec"))/1000)
            self.usbConnectHandler.digitalWrite(self.g_board_pin_relay, self.usbConnectHandler.LOW)
            log.debug(self.g_name + " Release button!")
            sleep(float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeToKeepButtonPressedMilliSec"))/1000)
            self.g_next_auto_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBeforeAutoRetryCloseDoor"))
            self.g_next_manual_cmd_allowed_time = time.time() + float(self.config_handler.getConfigParam("GARAGE_COMMON", "TimeBetweenButtonManualPressed"))
            self.g_last_cmd_sent_time=time.time()
            log.info("%s Open/Close door button pressed" % (self.g_name))
        except Exception:
            log.error("triggerGarageDoor Open or Close button problem !")
            traceback.print_exc()
            os._exit(-1)

        return True



    def printStatus(self):
        logstr = "%s:%s " % (self.g_name, self.g_status)
        sensor_status_str = ""

        all_light_status=self.getAllLightStatus()

        for sensor in self.g_sensor_props:
            sensor_status_str = sensor_status_str + sensor + "=" + self.g_sensor_props[sensor].status + " "

        if self.g_update_time != None:
            printut = datetime.datetime.fromtimestamp(self.g_update_time).strftime("%Y%m%d-%H%M%S")
        else:
            printut = "None"
        if self.g_open_time != None:
            printot = datetime.datetime.fromtimestamp(self.g_open_time).strftime("%Y%m%d-%H%M%S")
        else:
            printot = "None"
        if self.g_close_time != None:
            printct = datetime.datetime.fromtimestamp(self.g_close_time).strftime("%Y%m%d-%H%M%S")
        else:
            printct = "None"
        if self.g_error_time != None:
            printerrt = datetime.datetime.fromtimestamp(self.g_error_time).strftime("%Y%m%d-%H%M%S")
        else:
            printerrt = "None"
        if self.g_last_alert_time != None:
            printlast = datetime.datetime.fromtimestamp(self.g_last_alert_time).strftime("%Y%m%d-%H%M%S")
        else:
            printlast = "None"
        try:
            logstr = logstr + sensor_status_str + "updte=" + printut + " opn=" + printot + " clse=" + printct + " err=" + printerrt + " Alert=" + printlast + " Lights:" + all_light_status
            log.info(logstr)
        except Exception:
            log.error("Time Stamp print error ?!?  print to stdout ")
            print(logstr)

    def getAllLightStatus(self):
        all_light_status = ""
        for color in sorted({"GREEN", "RED", "WHITE"}):
            key_dev_color = self.g_name + "_" + color
            if key_dev_color in self.g_light_list:
                light_status = color[0]
                if self.g_light_list[key_dev_color].getLightStatus() == "ON":
                    all_light_status += light_status.lower()
                elif self.g_light_list[key_dev_color].getLightStatus() == "FLASH":
                    all_light_status += light_status.upper()
                else:
                    all_light_status += "-"
            else:
                log.debug("%s %s light defined yet" % (color,self.g_name))
        return all_light_status

    def test(self):
        self.initBoardPinModeOutput(self.g_board_pin_relay)
        logbuf = "Arduino Init Pin=%d" % self.g_board_pin_relay
        log.info(logbuf)
        for n in range(0, 1):
            self.usbConnectHandler.digitalWrite(self.g_board_pin_relay, self.usbConnectHandler.HIGH)
            log.info("ON")
            sleep(3)
            self.usbConnectHandler.digitalWrite(self.g_board_pin_relay, self.usbConnectHandler.LOW)
            log.info("OFF")
            sleep(2)
            n += 1
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", "test!")

        return resp