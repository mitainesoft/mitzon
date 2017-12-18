import logging
import os
import sys
import traceback
import collections

from GarageBackend.SingletonMeta import SingletonMeta
from GarageBackend.Constants import *
from GarageBackend.ConfigManager import ConfigManager
from GarageBackend.CommandQResponse import *
from GarageBackend.ConfigManager import ConfigManager
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

log = logging.getLogger('NotificationManager')



class NotificationManager(metaclass=SingletonMeta):
    def __init__(self):
        self.Notif = collections.namedtuple('Notif', ['sender', 'receipients', 'text', 'time'])
        self.config_handler = ConfigManager()
        self.alertfilename = self.config_handler.getConfigParam("INTERNAL", "ALERT_DEFINITION_FILE")
        self.alertFileListJSON = {}
        self.notifQueue = Queue()
        self.notif_enabled = self.config_handler.getConfigParam("NOTIFICATION_COMMON", "NotificationEnabled")
        self.default_language = self.config_handler.getConfigParam("NOTIFICATION_COMMON", "DEFAULT_LANGUAGE")

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
            mmmsg['Subject'] = "Alerte Garage %s" % (datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S"))
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
            os._exit(10)

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
                    id = alert_current_list[keyalert].id
                    alsev = self.alertFileListJSON[keylang][id]["severity"]

                    if alsev in self.config_handler.getConfigParam("NOTIFICATION_MANAGER", "NOTIFICATION_ALERT_SEVERITY_FILTER"):
                        alertfiltertrigger = True
                        log.debug("Accept notif by filter %s" % (id))
                    else:
                        log.debug("Skip notif low severity %s" % (id))
                        keyalert = keyiter.__next__()

                    nbrnotif_recipient += 1
                    tmptxt = "%d>Alert notif Key=%s %d" % (nbrnotif_recipient, keyalert, keyiter.__sizeof__())
                    log.debug(tmptxt)
                    nbrnotif += 1
                    altime = "%s" % datetime.datetime.fromtimestamp(int(alert_current_list[keyalert].time)).strftime(
                        "%Y%m%d-%H%M%S")

                    altext = self.alertFileListJSON[keylang][id]["text"]
                    alworkaround = self.alertFileListJSON[keylang][id]["workaround"]
                    # notif_sent


                    txt = "%d) %s\t%s -> %s (%s)" % (nbrnotif_recipient, alert_current_list[keyalert].device, altext, alworkaround, id)
                    alertlisttxt += "%s\n" % txt

                    keyalert = keyiter.__next__()

            except StopIteration:
                if (nbrnotif_recipient > 0):
                    alertlisttxt = alertlisttxt[:-1]
                else:
                    alertlisttxt = "---"
            except Exception:
                traceback.print_exc()
                log.error(alertlisttxt)
                os._exit(-1)

            if (alertfiltertrigger):
                #notif_text = "Msg from: " + sender + "\n\n" + alertlisttxt
                notif_text = "Attention!\n\n" + alertlisttxt
                self.notifQueue.put(self.Notif(sender, recipients, notif_text, time.time()))
                log.debug("Notif added to queue for " + recipients + " <<<" + notif_text + ">>>")
            else:
                log.debug("Skip notif message, no high sev !")
        log.debug("Send %d email notifications..." % nbrnotif)
        return
