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
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import configparser
from queue import *
import time
import datetime
import json
from time import sleep
import time
import datetime
import string


log = logging.getLogger('NotificationManager')

class NotificationManager(metaclass=SingletonMeta):
    def __init__(self):
        self.Notif = collections.namedtuple('Notif', ['sender', 'receipients', 'text', 'time'])
        self.config_handler = ConfigManager()
        # self.config_handler = ConfigManager()
        self.configfilename="config/notification_manager.config"
        self.nm_config = configparser.ConfigParser()
        self.nm_configSections = []
        self.readNMConfigFileName(self.configfilename)
        self.notifQueue = Queue()

        self.notif_enabled=self.config_handler.getConfigParam("NOTIFICATION_COMMON", "NotificationEnabled")
        self.default_language=self.config_handler.getConfigParam("GARAGE_COMMON", "DEFAULT_LANGUAGE")

        log.info("NotificationManager started...")


    def processnotif(self):
        i=0
        while (True):
            log.debug("** Notif Loop %d (q=%d) **" % (i,self.notifQueue.qsize()))
            while  not self.notifQueue.empty():
                try:
                    notif_obj=self.notifQueue.get(True,int(self.getConfigParam("NOTIFICATION_MANAGER","NOTIFICATION_MANAGER_LOOP_TIMEOUT")))
                    msg=notif_obj[2]
                    sender=notif_obj[0]
                    recipients=notif_obj[1]
                    logtxt=" Notif from %s to %s msg:<<<%s>>>" %(sender,recipients,msg)
                    log.info(logtxt)
                    if (self.notif_enabled.upper() == "TRUE"):
                        self.send_email(sender,recipients,msg)
                    else:
                        log.error("Notification disabled by config NOTIFICATION_MANAGER-->NotificationEnabled!")
                except Empty:
                    log.debug("notifQueue empty!?!?")
                    pass

            sleep(float(self.getConfigParam("NOTIFICATION_MANAGER","NOTIFICATION_MANAGER_LOOP_TIMEOUT")))
            i=i+1
        pass

    def send_email(self, sender, recipients, msg):
        try:
            COMMASPACE = ', '
            mmrecipients=recipients.split(',')
            log.info("Connecting to SMTP %s" % self.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "SMTP_SERVER"))
            self.email_server = smtplib.SMTP_SSL(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "SMTP_SERVER"), 465)
            self.email_server.ehlo()

            log.info("Login with %s" % self.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "USER"))

            self.email_server.login(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "USER"), \
                                    self.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "PASSWORD"))

            user_name=self.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "EMAIL_SENDER_NAME")

            log.info("Send email: <<%s>>" % msg)
            # subject = "Alerte Garage %s" % (datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S"))

            # mmmsg = MIMEMultipart()
            mmmsg=MIMEText(msg, 'plain')
            mmmsg['Subject']="Alerte Garage %s" % (datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S"))
            mmmsg['From'] = ("%s <%s>" % (user_name, sender))
            mmmsg['To'] = COMMASPACE.join(mmrecipients)

            # smtpmsg = ("From: %s\nTo: %s\nSubject: %s\n%s\n"
            #            % (sender, recipients, subject, msg))
            smtpmsg = mmmsg.as_string()
            # self.email_server.sendmail(sender, mmrecipients, smtpmsg)

            self.email_server.send_message(mmmsg)

            log.info("Close %s" % self.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "SMTP_SERVER"))
            self.email_server.close()
        except Exception:

            traceback.print_exc()
            log.error("Unable to send email notification !")
            self.email_server.close()
            os._exit(10)

    def send_email_legacy(self,sender,recipients,msg):
        try:
            log.info("Connecting to SMTP %s" % self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","SMTP_SERVER"))
            self.email_server = smtplib.SMTP_SSL(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","SMTP_SERVER"), 465)
            self.email_server.ehlo()

            log.info("Login with %s" % self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","USER"))

            self.email_server.login(self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","USER"), \
                                    self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","PASSWORD"))

            log.info("Send email: %s" % msg)
            subject="Alert Garage %s" % (datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S"))
            smtpmsg = ("From: %s\nTo: %s\nSubject: %s\n%s\n"
                   % (sender, recipients,subject,msg))

            self.email_server.sendmail(sender, recipients, smtpmsg)


            log.debug("Close %s"% self.getConfigParam("EMAIL_ACCOUNT_INFORMATION","SMTP_SERVER"))
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
            notif_text = "Msg from: " + sender + "\n\n" + txt
            self.notifQueue.put(self.Notif(sender, recipients,notif_text,time.time()))
            log.debug("Notif added to queue:" + notif_text )
        except Exception:
            traceback.print_exc()
            log.error(notif_text)
            os._exit(-1)

        log.debug("Add Notif Queue:" + sender+" receipeints:"+recipients+" txt:"+notif_text)
        return notif_text