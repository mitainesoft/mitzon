import logging
import collections
import sys
import traceback
import os
from GarageBackend.Constants import *
from GarageBackend.SingletonMeta import SingletonMeta
from GarageBackend.CommandQResponse import CommmandQResponse
from GarageBackend.ConfigManager import ConfigManager
import smtplib
import configparser
from queue import *
import time
import datetime
import json
from time import sleep
import time
import datetime


log = logging.getLogger('NotificationManager')

class NotificationManager(metaclass=SingletonMeta):
    def __init__(self):
        self.Notif = collections.namedtuple('Notif', ['sender', 'receipients', 'text', 'time'])

        # self.config_handler = ConfigManager()
        self.configfilename="config/notification_manager.config"
        self.nm_config = configparser.ConfigParser()
        self.nm_configSections = []
        self.readNMConfigFileName(self.configfilename)
        self.notifQueue = Queue()
        log.info("NotificationManager started...")


    def processnotif(self):
        i=0
        while (True):
            log.info("** Notif Loop %d (q=%d) **" % (i,self.notifQueue.qsize()))
            while  not self.notifQueue.empty():
                try:
                    notif_obj=self.notifQueue.get(True,int(self.getConfigParam("NOTIFICATION_MANAGER","NOTIFICATION_MANAGER_LOOP_TIMEOUT")))
                    msg=notif_obj[2]
                    sender=notif_obj[0]
                    recipients=notif_obj[1]
                    logtxt=" Notif from %s to %s msg=%s" %(sender,recipients,msg)
                    log.info(logtxt)
                    self.send_email(sender,recipients,msg)
                except Empty:
                    log.debug("notifQueue empty!?!?")
                    pass

            sleep(float(self.getConfigParam("NOTIFICATION_MANAGER","NOTIFICATION_MANAGER_LOOP_TIMEOUT")))
            i=i+1
        pass

    def send_email(self,sender,recipients,msg):
        try:
            log.info("Connecting to SMTP %s" % self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","SMTP_SERVER"))
            self.email_server = smtplib.SMTP_SSL(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","SMTP_SERVER"), 465)
            self.email_server.ehlo()

            log.info("Login with %s" % self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","USER"))

            self.email_server.login(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","USER"), \
                                    self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","PASSWORD"))

            log.info("Send msg %s" % msg)
            subject="Alert Garage %s" % (datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S"))
            smtpmsg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s\r\n\r\n"
                   % (sender, recipients,subject,msg))
            self.email_server.sendmail(sender, recipients, smtpmsg)


            log.info("Close %s"% self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","SMTP_SERVER"))
            self.email_server.close()
        except Exception:

            traceback.print_exc()
            log.error("Unable to send email notification !")
            self.email_server.close()
            os._exit(10)

    def readNMConfigFileName(self, filename):
        log.debug("Notif read config file name...")
        self.configfilename = filename
        try:
            with open(self.configfilename) as f:
                f.close()
        except IOError:
            log.error("NotificationManager Config file " + self.configfilename + " does not exist ! ")
            log.error("Exiting...")
            os._exit(-1)

        try:
            self.nm_config.read(self.configfilename)
            self.nm_configSections = self.nm_config.sections()
            for keySections in self.nm_configSections:
                 for key in self.nm_config[keySections]:
                    log.info(keySections + "/" + key + " = " + self.nm_config[keySections][key])

            pass
        except KeyError:
            log.info("Something went wrong while reading the NotificationManager config, Suspect is wrong file name or param")
            traceback.print_exc()
            os._exit(-1)
        except Exception:
            log.info("Something went wrong while reading the NotificationManager config, Suspect is wrong file name")
            traceback.print_exc()
            os._exit(-1)
            pass

    def getConfigParam(self, section, param):
        try:
            val = self.nm_config[section][param]
        except KeyError:
            log.error("Section=" + section + " param=" + param + " Not exist! Die !!!")
            traceback.print_exc()
            os._exit(-1)
        return val

    def addNotif(self, txt):
        try:
            sender=self.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "USER")
            recipients=self.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "RECIPIENTLIST")
            notif_text = "Msg from: " + sender + " " + txt
            self.notifQueue.put(self.Notif(sender, recipients,notif_text,time.time()))
            log.debug("Notif added to queue:" + notif_text )
        except Exception:
            traceback.print_exc()
            log.error(notif_text)
            os._exit(-1)

        log.debug("Add Notif Queue:" + sender+" receipeints:"+recipients+" txt:"+notif_text)
        return notif_text