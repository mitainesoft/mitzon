import logging
import os
import sys
import traceback
import collections

from MitzonBackend.SingletonMeta import SingletonMeta
from MitzonBackend.Constants import *
from MitzonBackend.ConfigManager import ConfigManager
from MitzonBackend.CommandQResponse import *
from MitzonBackend.ConfigManager import ConfigManager
from MitzonBackend.GarageUtil import *
import time
import datetime
from time import sleep

import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import configparser
from queue import *
import string
import json

log = logging.getLogger('Garage.NotificationManager')



class NotificationManager(metaclass=SingletonMeta):
    def __init__(self):
        self.Notif = collections.namedtuple('Notif', ['sender', 'receipients', 'text', 'time'])
        self.config_handler = ConfigManager()
        self.alertfilename = self.config_handler.getConfigParam("INTERNAL", "ALERT_DEFINITION_FILE")
        self.alertFileListJSON = {}
        self.notifQueue = Queue()
        self.notif_enabled = self.config_handler.getConfigParam("NOTIFICATION_COMMON", "NotificationEnabled")
        self.default_language = self.config_handler.getConfigParam("NOTIFICATION_COMMON", "DEFAULT_LANGUAGE")

        self.g_add_alert_time_by_type = {}  #Key is Alert type, data is time()
        self.TIME_BETWEEN_DUPLICATE_NOTIFICATION_EMAIL=float(self.config_handler.getConfigParam("NOTIFICATION_MANAGER", "TIME_BETWEEN_DUPLICATE_NOTIFICATION_EMAIL"))


        try:
            f = open(self.alertfilename)
            self.alertFileListJSON = json.load(f)
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

        log.info("NotificationManager started...")

    def processnotif(self):
        i = 0
        while (True):
            log.debug("** Notif Loop %d (q=%d) **" % (i, self.notifQueue.qsize()))
            while not self.notifQueue.empty():
                try:
                    notif_obj = self.notifQueue.get(True, int(self.config_handler.getConfigParam("NOTIFICATION_MANAGER", "NOTIFICATION_MANAGER_LOOP_TIMEOUT")))
                    msg = notif_obj[2]
                    sender = notif_obj[0]
                    recipients = notif_obj[1]

                    if (self.notif_enabled.upper() == "TRUE"):
                        logtxt = " Notif from %s to %s msg:<<<%s>>>" % (sender, recipients, msg)
                        log.debug(logtxt)
                        self.send_email(sender, recipients, msg)
                    else:
                        log.error("Notification disabled by config NOTIFICATION_MANAGER-->NotificationEnabled=False !")
                except Empty:
                    log.debug("notifQueue empty")
                    pass

            sleep(float(self.config_handler.getConfigParam("NOTIFICATION_MANAGER", "NOTIFICATION_MANAGER_LOOP_TIMEOUT")))
            i = i + 1

        pass

    def isAlertSentTooRecently(self, alertid, device, language=""):
        #self.g_last_alert_time = time.time()
        alert_sent_too_rencently=False
        key_email_recent=alertid+"_"+device+"_"+language
        status_text = "check if email sent too recently for %s %s %s (%s)" % (alertid, device, language,key_email_recent)
        log.debug(status_text)
        add_alert_time_by_typeTxt=""

        if (key_email_recent in self.g_add_alert_time_by_type):
            lastalerttime = self.g_add_alert_time_by_type[key_email_recent]
            add_alert_time_by_typeTxt = GarageUtil.getDateTimeFormated(self,lastalerttime) +"(exists)"
            if time.time() > (lastalerttime + self.TIME_BETWEEN_DUPLICATE_NOTIFICATION_EMAIL):
                try:
                    #del self.g_add_alert_time_by_type[key_email_recent]
                    self.g_add_alert_time_by_type[key_email_recent] = time.time()
                    alert_sent_too_rencently = False
                    #Alarm not cleared will eventually be sent again !
                    log.info("%s for %s can now be emailed again since not sent for at least %ds !" % (alertid, device, self.TIME_BETWEEN_DUPLICATE_NOTIFICATION_EMAIL))
                except KeyError:
                    pass
            else:
                alert_sent_too_rencently=True
                log.debug("Skip email related to %s %s %s (time between=%ds)" % (alertid,device,language,self.TIME_BETWEEN_DUPLICATE_NOTIFICATION_EMAIL))
        else:
            #Email not duplicate
            alert_sent_too_rencently = False
            self.g_add_alert_time_by_type[key_email_recent] = time.time()
            add_alert_time_by_typeTxt = GarageUtil.getDateTimeFormated(self,self.g_add_alert_time_by_type[key_email_recent])
            log.debug("email related to %s %s NOT a duplicate (time between=%ds)" % (alertid, device,self.TIME_BETWEEN_DUPLICATE_NOTIFICATION_EMAIL))
        logtxt = "isAlertSentTooRecently "+GarageUtil.getTrueFalseStr(self,alert_sent_too_rencently)+" "+key_email_recent \
                                  + " alert_time_by_type=" + add_alert_time_by_typeTxt +"("+alertid+")"


        log.debug(logtxt)
        return alert_sent_too_rencently

    def send_email(self, sender, recipients, msg):
        try:
            COMMASPACE = ', '
            mmrecipients = recipients.split(',')
            log.debug("Connecting to SMTP %s" % self.config_handler.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "SMTP_SERVER"))
            # TODO make 465 configurable
            self.email_server = smtplib.SMTP_SSL(self.config_handler.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "SMTP_SERVER"), 465)
            self.email_server.ehlo()

            log.debug("Login with %s" % self.config_handler.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "USER"))

            self.email_server.login(self.config_handler.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "USER"), \
                                    self.config_handler.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "PASSWORD"))

            user_name = self.config_handler.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "EMAIL_SENDER_NAME")

            #print a one line in logs
            tmptxt=msg.replace("\n", " ** ")
            log.info("Send email: <<%s>>" % tmptxt)
            # subject = "Alerte Garage %s" % (datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S"))

            # mmmsg = MIMEMultipart()
            mmmsg = MIMEText(msg, 'plain')
            mmmsg['Subject'] = "Alerte Garage et Gazon %s" % (datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S"))
            mmmsg['From'] = ("%s <%s>" % (user_name, sender))
            mmmsg['To'] = COMMASPACE.join(mmrecipients)

            smtpmsg = mmmsg.as_string()
            self.email_server.send_message(mmmsg)

            log.debug("Close %s" % self.config_handler.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "SMTP_SERVER"))
            self.email_server.close()
        except Exception:

            traceback.print_exc()
            log.error("Unable to send email notification ! open ports for DNS and emails on firewall ? Check README.rst  ")
            self.email_server.close()

    def addNotif(self, alert_current_list):
        nbrnotif = 0;
        clmax = 10
        alertfiltertrigger = False
        recipientsHash = {}  # Key is language

        sender = self.config_handler.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "USER")

        recipient_email_lang_str = self.config_handler.getConfigParam("EMAIL_ACCOUNT_INFORMATION", "RECIPIENTLIST")
        recipient_email_lang_arr = recipient_email_lang_str.split(',')

        for email_lang in recipient_email_lang_arr:
            email_lang_arr = email_lang.split('+')
            lang = self.default_language
            if len(email_lang_arr) == 2:
                email_addr = email_lang_arr[0]
                lang = email_lang_arr[1]
            elif len(email_lang_arr) == 1:
                email_addr = email_lang_arr[0]
                lang = self.default_language
            else:
                log.error("Bad format email and language. Ignore %s %s" % (email_addr, lang))

            if lang in recipientsHash:
                recipientsHash[lang] += email_addr + ","
            else:
                recipientsHash[lang] = email_addr + ","
            log.debug("AddNotif email:%s lang:%s recipientsHash:%s" % (email_addr, lang, recipientsHash[lang]))

        lang_bookmarks = self.alertFileListJSON.keys()

        for keylang in recipientsHash:
            alertlisttxt = "Liste Alerte:\n"
            recipients = recipientsHash[keylang][:-1]  # chomp comma
            nbrnotif_recipient = 0

            try:
                keyiter = iter(alert_current_list)
                keyalert = keyiter.__next__()  # Goto except StopIteration if empty
                while keyalert != None and nbrnotif < clmax:
                    alert_sent_too_recently=False
                    id = alert_current_list[keyalert].id
                    device = alert_current_list[keyalert].device
                    alsev = self.alertFileListJSON[keylang][id]["severity"]
                    altime = "%s" % datetime.datetime.fromtimestamp(int(alert_current_list[keyalert].time)).strftime(
                        "%Y%m%d-%H%M%S")

                    if self.isAlertSentTooRecently(id,device,keylang)==True:
                        log.debug("Skip %s duplicate email notif for %s (%s)" % (id,device,keylang))
                        keyalert = keyiter.__next__()

                    if alsev in self.config_handler.getConfigParam("NOTIFICATION_MANAGER", "NOTIFICATION_ALERT_SEVERITY_FILTER"):
                        alertfiltertrigger = True
                        log.debug("Accept notif by filter %s %s %s" % (id, device, alsev))
                    else:
                        log.debug("Skip notif low severity %s %s %s" % (id,device, alsev))
                        keyalert = keyiter.__next__()

                    nbrnotif_recipient += 1
                    tmptxt = "%d>Alert notif Key=%s %d" % (nbrnotif_recipient, keyalert, keyiter.__sizeof__())
                    log.debug(tmptxt)
                    # nbrnotif += 1


                    altext = self.alertFileListJSON[keylang][id]["text"]
                    alworkaround = self.alertFileListJSON[keylang][id]["workaround"]
                    # notif_sent


                    txt = "%d) %s\t%s -> %s (%s)" % (nbrnotif_recipient, alert_current_list[keyalert].device, altext, alworkaround, id)
                    alertlisttxt += "%s\n" % txt

                    nbrnotif += 1
                    keyalert = keyiter.__next__()

            except StopIteration:
                if (nbrnotif_recipient > 0):
                    alertlisttxt = alertlisttxt[:-1]
                else:
                    alertlisttxt = "---"
            except Exception:
                log.error("Exception during email processing")
                traceback.print_exc()
                #os._exit(-1)

            if (alertfiltertrigger == True):
                #notif_text = "Msg from: " + sender + "\n\n" + alertlisttxt
                notif_text = "Attention!\n\n" + alertlisttxt
                self.notifQueue.put(self.Notif(sender, recipients, notif_text, time.time()))
                log.debug("Notif added to queue for " + recipients + " <<<" + notif_text + ">>>")
            else:
                log.debug("Skip notif message, no high sev !")
        log.debug("addNotif Send %d email notifications... (alertfiltertrigger:%s)" % (nbrnotif,GarageUtil.getTrueFalseStr(self,alertfiltertrigger)))
        return
