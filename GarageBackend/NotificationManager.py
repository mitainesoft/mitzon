import logging
import collections
from GarageBackend.Constants import *
from GarageBackend.CommandQResponse import *
from GarageBackend.SingletonMeta import SingletonMeta
from GarageBackend.CommandQResponse import *
from GarageBackend.AlertManager import AlertManager
from GarageBackend.ConfigManager import *
import smtplib
from queue import *
import time
import datetime
import json
from time import sleep
import time
import datetime


log = logging.getLogger('NotificationManager')

class NotificationManager():
    def __init__(self):
        # self.config_handler = ConfigManager()
        self.configfilename="config/notification_manager.config"
        self.nm_config = configparser.ConfigParser()
        self.nm_configSections = []
        self.readNMConfigFileName(self.configfilename)
        log.info("NotificationManager started...")

    def processnotif(self):
        i=0
        while (True):
            log.info("** Notif Loop %d **" % i)
            sleep(float(self.getConfigParam("NOTIFICATION_MANAGER","NOTIFICATION_MANAGER_LOOP_TIMEOUT")))
            i=i+1
        pass

    def readNMConfigFileName(self, filename):
        log.info("Set config file name...")
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