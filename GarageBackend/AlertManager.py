import logging
import collections
from GarageBackend.Constants import *
from GarageBackend.CommandQResponse import *
from GarageBackend.SingletonMeta import SingletonMeta
from GarageBackend.CommandQResponse import *
from GarageBackend.ConfigManager import *
from queue import *
import time
import datetime
import json

log = logging.getLogger('garageCmdProcessor')


class AlertManager(metaclass=SingletonMeta):


    def __init__(self):
        self.config_handler = ConfigManager()
        self.alertfilename="config/event_list_en.json"
        log.info("AlertManager started...")
        self.s_id = -1
        self.s_status = G_UNKNOWN
        self.s_board_pin = 7
        self.s_name = "[UNKNOWN]"
        self.alertFileListJSON = {}
        self.alertCurrentList = {}
        self.Alert = collections.namedtuple('Alert', ['id', 'device', 'severity', 'category', 'text', 'time'])

        try:
            f=open(self.alertfilename)
            self.alertFileListJSON=json.load(f)
            f.close()
            pass
        except IOError:
            log.error("Config file " + self.alertfilename + " does not exist ! ")
            log.error("Exiting...")
            os._exit(-1)
        except Exception:
            traceback.print_exc()
            log.error("Exiting...")
            os._exit(-1)

    #required for subcriber
    def processDeviceCommand(self, mything, myservice, myid):
        # log.info(str(self.deviceList))
        logbuf = "AlertManager Cmd Received: %s/%s/%s " % (mything, myservice, myid)
        log.info(logbuf)
        resp = CommmandQResponse(0,"Alert=None")
        return (resp)

    def enableSiren(self,mything,myservice,myid):
        isgarageopen= True
        return isgarageopen

    def addAlert(self, id, device,extratxt=""):
        try:
            alert_text = device + " " + self.alertFileListJSON[id]["text"]+" "+extratxt
            keyalert=id+"_"+device
            self.alertCurrentList[keyalert] = self.Alert(id,device,self.alertFileListJSON[id]["severity"],
                                                         self.alertFileListJSON[id]["category"],self.alertFileListJSON[id]["text"],time.time())
        except Exception:
            traceback.print_exc()
            log.error(alert_text)
            os._exit(-1)

        log.warning("Add Alert Queue: " + id+">"+alert_text)
        return alert_text


    def clearAllAlert(self):
        self.alertCurrentList.clear()
        log.warning("Alert Queue Blindly Cleared (need to improve!!!)!!!")

    def clearAlertDevice(self,cat,dev):
        log.debug("Clear alert request " + cat + " for " + dev)

        crazyloop=0;
        keyiter=iter(self.alertCurrentList)
        clmax=500
        try:
            keyalert = keyiter.__next__()
            while keyalert != None and crazyloop<clmax:
                tmptxt="%d>Alert Key=%s %d" %(crazyloop,keyalert,keyiter.__sizeof__())
                log.debug(tmptxt)
                crazyloop += 1
                if dev == self.alertCurrentList[keyalert].device and cat==self.alertCurrentList[keyalert].category:
                    altime = "%s" % datetime.datetime.fromtimestamp(int(self.alertCurrentList[keyalert].time)).strftime(
                        "%Y%m%d-%H%M%S")
                    txt = "Alert id:%s dev:%s sev:%s cat:%s text:%s time:%s " % (
                    self.alertCurrentList[keyalert].id, self.alertCurrentList[keyalert].device, \
                    self.alertCurrentList[keyalert].severity, self.alertCurrentList[keyalert].category,
                    self.alertCurrentList[keyalert].text, altime)
                    log.info("Clear alert " + cat + " for " + dev + "-->" + txt)
                    del self.alertCurrentList[keyalert]
                keyalert = keyiter.__next__()
            if (crazyloop>=clmax):
                os._exit(clmax)
        except StopIteration:
            log.debug("Alarm List empty StopIteration!")
        except Exception:
            # traceback.print_exc()
            log.debug("Alarm List empty Exception!")

    def clearAlertID(self, id_to_clear,dev ):
        log.debug("Clear alert ID request " + id_to_clear + " for " + dev)

        crazyloop = 0;
        keyiter = iter(self.alertCurrentList)
        clmax = 500
        try:
            keyalert = keyiter.__next__()
            while keyalert != None and crazyloop < clmax:
                tmptxt = "%d>Alert Key=%s %d" % (crazyloop, keyalert, keyiter.__sizeof__())
                log.debug(tmptxt)
                crazyloop += 1
                if id_to_clear == self.alertCurrentList[keyalert].id and dev == self.alertCurrentList[keyalert].device:
                    altime = "%s" % datetime.datetime.fromtimestamp(int(self.alertCurrentList[keyalert].time)).strftime(
                        "%Y%m%d-%H%M%S")
                    txt = "Alert id:%s dev:%s sev:%s cat:%s text:%s time:%s " % (
                        self.alertCurrentList[keyalert].id, self.alertCurrentList[keyalert].device, \
                        self.alertCurrentList[keyalert].severity, self.alertCurrentList[keyalert].category, \
                        self.alertCurrentList[keyalert].text, altime)
                    log.info("Clear alert ID " + id_to_clear + " for " + dev + "-->" + txt)
                    del self.alertCurrentList[keyalert]
                keyalert = keyiter.__next__()
            if (crazyloop >= clmax):
                os._exit(clmax)
        except StopIteration:
            log.debug("Alarm List empty StopIteration!")
        except Exception:
            # traceback.print_exc()
            log.debug("Alarm List empty Exception!")

    def test(self):

        return CommmandQResponse(0, "test AlertManager")

    def status(self):
        nbralerts=self.alertCurrentList.__len__()

        try:
            if nbralerts>0:
                log.info("AlertManager status: %d alerts", (nbralerts))
                for keyalert in self.alertCurrentList:
                    altime="%s" % datetime.datetime.fromtimestamp(int(self.alertCurrentList[keyalert].time)).strftime("%Y%m%d-%H%M%S")
                    txt="Alert id:%s %s sev:%s cat:%s text:%s time:%s " % (self.alertCurrentList[keyalert].id,self.alertCurrentList[keyalert].device,\
                                                                    self.alertCurrentList[keyalert].severity,self.alertCurrentList[keyalert].category,\
                                                                    self.alertCurrentList[keyalert].text,altime)
                    # +" time:"+ altime

                    log.info(txt)
        except  Exception:
            traceback.print_exc()
            log.error("Unable to print alarm list !")
            os._exit(-1)
        resp = CommmandQResponse(0,"status AlertManager" )
        return (resp)
