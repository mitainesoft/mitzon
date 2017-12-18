import logging
import collections
import os
import sys
import traceback
from GarageBackend.Constants import *
from GarageBackend.CommandQResponse import CommmandQResponse
from GarageBackend.SingletonMeta import SingletonMeta
from GarageBackend.ConfigManager import ConfigManager
from GarageBackend.NotificationManager import NotificationManager
from queue import *
import time
import datetime
import json



log = logging.getLogger('AlertManager')


class AlertManager(metaclass=SingletonMeta):
    def __init__(self):
        self.config_handler = ConfigManager()
        self.notif_handler = NotificationManager()
        self.alertfilename=self.config_handler.getConfigParam("INTERNAL", "ALERT_DEFINITION_FILE")
        log.info("AlertManager started...")
        self.default_language=self.config_handler.getConfigParam("NOTIFICATION_COMMON", "DEFAULT_LANGUAGE")

        self.alertFileListJSON = {}
        self.alertCurrentList = {}
        self.Alert = collections.namedtuple('Alert', ['id', 'device', 'severity', 'category', 'text', 'workaround', 'time','notif_sent'])

        #Time supervision
        self.last_alert_sent_time=0
        self.seconds_between_alerts=float(self.config_handler.getConfigParam("ALERT", "TimeBetweenAlerts"))

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


    def processAlerts(self):
        alert_triggered=False
        keyiter = iter(self.alertCurrentList)
        try:
            keyalert = keyiter.__next__()
            if keyalert != None:
                alert_triggered=True
        except StopIteration:
            log.debug("processAlerts Alarm List empty StopIteration!")
        except Exception:
            traceback.print_exc()
            log.error("processAlerts Alarm List empty Exception! Should not be here !")

        #Send Alert?!?
        if (alert_triggered == True):
            if self.isAlertToBeSent() == True:
                log.debug("Sending '%d' Alerts Notification thread" % len(self.alertCurrentList))
                self.notif_handler.addNotif(self.alertCurrentList)

        return (alert_triggered)

    def isAlertToBeSent(self):
        sendalert=False
        forcesendAlert = True  #for debug purposes !!!
        lastalerttime = "%s" % datetime.datetime.fromtimestamp(int(self.last_alert_sent_time)).strftime("%Y%m%d-%H%M%S")
        tmpmsg= "Last Alert sent at %s" % lastalerttime
        try:
            #Last check if any alarms left due to some racing condition
            keyiter = iter(self.alertCurrentList)
            keyalert = keyiter.__next__()
            if (forcesendAlert==True or (time.time() > (self.last_alert_sent_time + self.seconds_between_alerts))):
                prev_alert_time = self.last_alert_sent_time
                self.last_alert_sent_time = time.time()
                nbrmin= int((self.last_alert_sent_time-prev_alert_time))/60
                tmpmsg = tmpmsg + (" last alert sent %d minutes ago" % nbrmin)
                log.debug("Alert send authorized. " + tmpmsg)
                sendalert = True
            else:
                tmpmsg = tmpmsg + (" (Time between alerts:%dsec)" % self.seconds_between_alerts )
                log.debug("Alert Send denied! "+tmpmsg)
        except StopIteration:
            log.info("No alert left due to racing condition. Alert send denied! " +tmpmsg )
        except Exception:
            log.error("Alert!  Unexpected code condition! Die! " + tmpmsg)
            traceback.print_exc()
            os._exit(-1)

        if (sendalert==False):
            log.debug("No alert to send. " + tmpmsg)

        return sendalert

    #required for subcriber
    def processDeviceCommand(self, mything, myservice, myid):
        # log.info(str(self.deviceList))
        logbuf = "AlertManager processDeviceCommand cmd Received: %s/%s/%s " % (mything, myservice, myid)
        log.debug(logbuf)

        try:
            log.debug("Calling %s " % (self.__class__.__name__))
            thingToCall = getattr(self, myservice)
            resp = thingToCall()
        except AttributeError:
            resp = CommmandQResponse(time.time(), "Alert Manager Ok")
        # resp = CommmandQResponse(time.time(),alertlisttxt)
        return (resp)

    def enableSiren(self,mything,myservice,myid):
        isgarageopen= True
        return isgarageopen

    def addAlert(self, id, device,extratxt=""):
        try:
            alert_text = device + " " + self.alertFileListJSON[self.default_language][id]["text"]+" "+extratxt
            keyalert=id+"_"+device
            self.alertCurrentList[keyalert] = self.Alert(id,device,self.alertFileListJSON[self.default_language][id]["severity"],
                                                         self.alertFileListJSON[self.default_language][id]["category"],
                                                         self.alertFileListJSON[self.default_language][id]["text"],
                                                         self.alertFileListJSON[self.default_language][id]["workaround"],
                                                         time.time(),None)
        except Exception:
            traceback.print_exc()
            log.error(alert_text)
            os._exit(-1)

        log.debug("Add Alert Queue: " + id+">"+alert_text)
        return alert_text

    def clear(self):
        # Not called  Bug !
        self.clearAllAlert()
        resp = CommmandQResponse(time.time()*1000000, "AlertManager alarm cleared" )
        return (resp)

    def clearAllAlert(self):
        self.alertCurrentList.clear()
        log.warning("All Alerts cleared!")

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
                    log.debug("Clear alert " + cat + " for " + dev + "-->" + txt)
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
                    log.debug("Clear alert ID " + id_to_clear + " for " + dev + "-->" + txt)
                    del self.alertCurrentList[keyalert]
                keyalert = keyiter.__next__()
            if (crazyloop >= clmax):
                os._exit(clmax)
        except StopIteration:
            log.debug("Alarm List empty StopIteration!")
        except Exception:
            # traceback.print_exc()
            log.debug("Alarm List empty Exception!")

    def clearAlertNotifSent(self, dev):
        log.debug("Clear alert Notif Sent for " + dev)

        crazyloop = 0;
        keyiter = iter(self.alertCurrentList)
        clmax = 100
        try:
            keyalert = keyiter.__next__()
            while keyalert != None and crazyloop < clmax:
                tmptxt = "%d>Alert Key=%s %d" % (crazyloop, keyalert, keyiter.__sizeof__())
                log.debug(tmptxt)
                crazyloop += 1
                if self.alertCurrentList[keyalert].alert_sent != None:
                    altime = "%s" % datetime.datetime.fromtimestamp(int(self.alertCurrentList[keyalert].time)).strftime(
                        "%Y%m%d-%H%M%S")
                    nstime = "%s" % datetime.datetime.fromtimestamp(int(self.alertCurrentList[keyalert].notif_sent)).strftime(
                        "%Y%m%d-%H%M%S")
                    txt = "Alert id:%s dev:%s sev:%s cat:%s text:%s time:%s Notif:%s" % (
                        self.alertCurrentList[keyalert].id, self.alertCurrentList[keyalert].device, \
                        self.alertCurrentList[keyalert].severity, self.alertCurrentList[keyalert].category, \
                        self.alertCurrentList[keyalert].text, altime, nstime)
                    log.debug("Clear alert Notif Sent for " + dev + "-->" + txt)
                    del self.alertCurrentList[keyalert]
                keyalert = keyiter.__next__()
            if (crazyloop >= clmax):
                log.fatal("Too many alerts ! Die !")
                os._exit(clmax)
        except StopIteration:
            log.debug("Alarm List empty StopIteration!")
        except Exception:
            # traceback.print_exc()
            log.debug("Alarm List empty Exception!")

    def test(self):

        return CommmandQResponse(0, "test AlertManager")

    def status(self):

        alertlisttxt="Alertlist="

        crazyloop=0;
        keyiter=iter(self.alertCurrentList)
        clmax=500
        try:
            keyalert = keyiter.__next__()
            while keyalert != None and crazyloop<clmax:
                tmptxt="%d>Alert Key=%s %d" %(crazyloop,keyalert,keyiter.__sizeof__())
                log.debug(tmptxt)
                crazyloop += 1
                altime = "%s" % datetime.datetime.fromtimestamp(int(self.alertCurrentList[keyalert].time)).strftime(
                    "%Y%m%d-%H%M%S")
                txt = "Alert id:%s dev:%s sev:%s cat:%s text:%s workaround:%s time:%s " % (
                self.alertCurrentList[keyalert].id, self.alertCurrentList[keyalert].device, \
                self.alertCurrentList[keyalert].severity, self.alertCurrentList[keyalert].category,
                self.alertCurrentList[keyalert].text,self.alertCurrentList[keyalert].workaround, altime)
                alertlisttxt += "%s;" % txt
                keyalert = keyiter.__next__()
                crazyloop+=1
            if (crazyloop>=clmax):
                os._exit(clmax)
        except StopIteration:
            if(crazyloop>0):
                alertlisttxt=alertlisttxt[:-1]
            else:
                alertlisttxt = "Alertlist=None"
            log.debug("processDeviceCommand Alarm List empty StopIteration!")
        except Exception:
            # traceback.print_exc()
            log.error("processDeviceCommand Alarm List empty Exception! Should not be here !")

        resp = CommmandQResponse(time.time(),"[AlertManager] "+ alertlisttxt )
        # resp = CommmandQResponse(time.time() * 1000000, "[DeviceManager] "+self.determineGarageDoorOpenClosedStatus().getRspPropsToString())

        return (resp)
