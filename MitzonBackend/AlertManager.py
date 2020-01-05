import logging
import collections
import os
import sys
import traceback
from MitzonBackend.Constants import *
from MitzonBackend.CommandQResponse import CommmandQResponse
from MitzonBackend.SingletonMeta import SingletonMeta
from MitzonBackend.ConfigManager import ConfigManager
from MitzonBackend.NotificationManager import NotificationManager
from queue import *
import time
import datetime
import json



log = logging.getLogger('Garage.AlertManager')


class AlertManager(metaclass=SingletonMeta):
    def __init__(self):
        #log.setLevel(logging.INFO)
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

        self.autoClearAlertByList()
        return (alert_triggered)

    def isAlertToBeSent(self):
        sendalert=False
        tmpmsg=""
        forcesendAlert = False  #for debug purposes !!!
        lastalerttime = "%s" % datetime.datetime.fromtimestamp(int(self.last_alert_sent_time)).strftime("%Y%m%d-%H%M%S")
        if self.last_alert_sent_time>0:
            tmpmsg= "Last Alert sent at %s" % lastalerttime
        tmp_alert_id_txt=""
        try:
            #Last check if any alarms left due to some racing condition
            keyiter = iter(self.alertCurrentList)
            keyalert = keyiter.__next__()
            tmp_alert_id_txt = self.alertCurrentList[keyalert].id
            if tmp_alert_id_txt == None:
                tmp_alert_id_txt="[None]"
            if (forcesendAlert==True or (time.time() > (self.last_alert_sent_time + self.seconds_between_alerts))):
                prev_alert_time = self.last_alert_sent_time
                self.last_alert_sent_time = time.time()
                if (prev_alert_time>0):
                    nbrmin= int((self.last_alert_sent_time-prev_alert_time))/60
                    tmpmsg = tmpmsg + (" last alert sent %d minutes ago" % nbrmin)
                log.debug("Alert %s send authorized if not filtered out. %s" % (tmp_alert_id_txt,tmpmsg))
                sendalert = True
            else:
                tmpmsg = tmpmsg + (" (Time between alerts:%dsec)" % self.seconds_between_alerts )
                log.debug("Alert %s Send denied! %s" %(tmp_alert_id_txt,tmpmsg))
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
            # self.tid, self.module, self.device, self.status, self.text
            #resp = CommmandQResponse(time.time(), "Alert Manager Ok")
            resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", "Alert Manager Ok")
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
        #resp = CommmandQResponse(time.time()*1000000, "AlertManager alarm cleared" )
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", "AlertManager alarm cleared" )
        return (resp)

    def clearAllAlert(self):
        self.alertCurrentList.clear()
        log.warning("All Alerts cleared!")

    def clearAlertDevice(self,cat,dev):
        rc="Clear alert request " + cat + " for " + dev
        log.debug(rc)

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
            logtxt = "1-OK! StopIteration traceback:" + str(traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.debug(logtxt)
        except RuntimeError:
            logtxt = "1-OK! RuntimeError traceback:" + str(traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.debug(logtxt)
            # expected dictionary changed size during iteration
        except Exception:
            #traceback.print_exc()
            logtxt = "1-Exception traceback:" + str(traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.error(logtxt)

        return rc

    def autoClearAlertByList(self):
        rc = "Auto Clear Alert By List called for: " + self.config_handler.getConfigParam("ALERT", "AlertAutoClearList")
        log.debug(rc)
        #Clears one at the time !
        crazyloop = 0;
        keyiter = iter(self.alertCurrentList)
        clmax = 500
        try:
            keyalert = keyiter.__next__()
            while keyalert != None and crazyloop < clmax:
                id=self.alertCurrentList[keyalert].id
                altime = "%s" % datetime.datetime.fromtimestamp(int(self.alertCurrentList[keyalert].time)).strftime(
                    "%Y%m%d-%H%M%S")
                crazyloop += 1


                if (id in self.config_handler.getConfigParam("ALERT", "AlertAutoClearList")):
                    log.debug("auto Clear Alert By List %s %s %d triggered!" %(id,altime,float(self.alertCurrentList[keyalert].time)))

                if id in self.config_handler.getConfigParam("ALERT", "AlertAutoClearList") \
                    and time.time() > (float(self.alertCurrentList[keyalert].time)+float(self.config_handler.getConfigParam("ALERT", "AlertDefaultClearInterval"))):

                    txt = "Alert id:%s dev:%s sev:%s cat:%s text:%s time:%s " % (
                        self.alertCurrentList[keyalert].id, self.alertCurrentList[keyalert].device, \
                        self.alertCurrentList[keyalert].severity, self.alertCurrentList[keyalert].category, \
                        self.alertCurrentList[keyalert].text, altime)
                    log.info("Auto Clear Alert %s done!" % (txt))
                    del self.alertCurrentList[keyalert]
                keyalert = keyiter.__next__()
            if (crazyloop >= clmax):
                os._exit(clmax)
        except StopIteration:
            logtxt = "2-OK! StopIteration traceback:" + str(traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.debug(logtxt)
        except RuntimeError:
            logtxt = "2-OK! RuntimeError traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.debug(logtxt)
            # expected dictionary changed size during iteration
        except Exception:
            # traceback.print_exc()
            logtxt = "2-Exception traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.error(logtxt)

        return rc

    def clearAlertID(self, id_to_clear,dev ):
        rc = "Clear alert ID request " + id_to_clear + " for " + dev
        log.debug(rc)

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
            logtxt = "3-OK! StopIteration traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.debug(logtxt)
        except RuntimeError:
            logtxt = "3-OK! RuntimeError traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.debug(logtxt)
            # expected dictionary changed size during iteration
        except Exception:
            # traceback.print_exc()
            logtxt = "3-Exception traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.error(logtxt)

        return rc

    def clearAlertNotifSent(self, dev):
        rc = "Clear alert Notif Sent for " + dev
        log.debug(rc)

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
            logtxt = "4-OK! StopIteration traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.debug(logtxt)
        except RuntimeError:
            logtxt = "4-OK! RuntimeError traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.debug(logtxt)
            # expected dictionary changed size during iteration
        except Exception:
            # traceback.print_exc()
            logtxt = "4-Exception traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.error(logtxt)

        return rc

    def test(self):
        resp = CommmandQResponse(time.time() * 1000000, "[MESSAGE]", "", "", "test AlertManager")
        return resp


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
            logtxt = "5-OK! StopIteration traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.debug(logtxt)
        except RuntimeError:
            logtxt = "5-OK! RuntimeError traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.debug(logtxt)
            # expected dictionary changed size during iteration
        except Exception:
            # traceback.print_exc()
            logtxt = "5-Exception traceback:" + str(
                traceback.format_list(traceback.extract_stack())) + "    sys.excInfo:" + str(sys.exc_info())
            log.error(logtxt)

        resp = CommmandQResponse(time.time() * 1000000,"[AlertManager]","","",alertlisttxt )
        # resp = CommmandQResponse(time.time() * 1000000, "[DeviceManager] "+self.determineGarageDoorOpenClosedStatus().getRspPropsToString())

        return (resp)
