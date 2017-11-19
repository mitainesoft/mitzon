""" Read Building definifion from file"""
import logging
from GarageBackend.Constants import *
import configparser
from GarageBackend.SingletonMeta import SingletonMeta
import traceback
import sys
import os
import re

log = logging.getLogger('ConfigManager')

class ConfigManager(metaclass=SingletonMeta):

    def __init__(self):
        log.debug("Started...")
        self.configfilename="config/garage_backend.config"
        self.config = configparser.ConfigParser()
        self.configSections = []
        self.NBR_GARAGE=0 #Calculated value
        self.GARAGE_NAME = [] # ["GARAGE_0", "GARAGE_1", "GARAGE_2", "GARAGE_3"]

    def setConfigFileName(self,filename):
        log.debug("Set config file name...")
        self.configfilename = filename
        try:
            with open(self.configfilename) as f:
                f.close()
        except IOError:
            log.error("Config file " + self.configfilename + " does not exist ! ")
            log.error("Exiting...")
            os._exit(-1)

        try:
            # config = configparser.ConfigParser()
            self.config.read(self.configfilename)
            self.configSections=self.config.sections()
            for keySections in self.configSections:
                if ("GARAGE_" in keySections):
                    matchObj=re.match("GARAGE_\d",keySections,2)
                    if matchObj:
                        if (self.getConfigParam(keySections, "SuperviseThisGarage").upper() == "TRUE"):
                            self.GARAGE_NAME.append(keySections)
                            self.NBR_GARAGE+=1
                            log.info("Found garage in config:" + keySections +" ("+self.NBR_GARAGE.__str__()+")")
                        else:
                            log.info("Skip garage in config:" + keySections + ". Should not supervise!")
                    else:
                        log.debug("config file, not garage: " + keySections + "...Skipping" )
                for key in self.config[keySections]:
                    log.info(keySections + "/" + key + " = " + self.config[keySections][key])
            self.validateParamsUsed()
        except KeyError:
            log.info("Something went wrong while reading the config, Suspect is wrong file name or param")
            traceback.print_exc()
            os._exit(-1)
        except Exception:
            log.info("Something went wrong while reading the config, Suspect is wrong file name")
            traceback.print_exc()
            os._exit(-1)
            pass

    def getConfigParam(self,section,param):
        try:
            val=self.config[section][param]
        except KeyError:
            log.error("Section="+section+" param=" + param +" Not exist! Die !!!")
            traceback.print_exc()
            os._exit(-1)
        return val

    def validateParamsUsed(self):
        section=""
        param=""
        configParamsUsedinCodeArray = [
            ['GARAGE_MANAGER', 'garage_manager_loop_timeout'],
            ['GARAGE_MANAGER', 'sensor_defect_assessment_time'],
            ['GARAGE_MANAGER', 'garage_name_for_test'],
            ['THREAD_CONTROL', 'resp_timeout'],
            ['GARAGE_COMMON', 'garageopentriggeralarmelapsedtime'],
            ['GARAGE_COMMON', 'garageopentriggerclosedoorelapsedtime'],
            ['GARAGE_COMMON', 'lightgarageopentriggerclosedoorprewarningbeforeclose'],
            ['GARAGE_COMMON', 'garagelockopentriggeralarmelapsedtime'],
            ['GARAGE_COMMON', 'garagedoorassumedclosedtime'],
            ['GARAGE_COMMON', 'timetokeepbuttonpressedmillisec'],
            ['GARAGE_COMMON', 'timebeforeautoretryclosedoor'],
            ['GARAGE_COMMON', 'timebetweenbuttonmanualpressed'],
            ['GARAGE_COMMON', 'garageelapsedtimeforstatuschange'],
            ['GARAGE_COMMON', 'garagerelaylowenable'],
            ['GARAGE_0', 'supervisethisgarage'],
            ['GARAGE_0', 'garageboardpin'],
            ['GARAGE_0', 'garagesensorsboardpin'],
            ['GARAGE_0', 'garagegreenlightboardpin'],
            ['GARAGE_0', 'garageredlightboardpin'],
            ['GARAGE_0', 'garagewhitelightboardpin'],
            ['GARAGE_1', 'supervisethisgarage'],
            ['GARAGE_1', 'garageboardpin'],
            ['GARAGE_1', 'garagesensorsboardpin'],
            ['GARAGE_1', 'garagegreenlightboardpin'],
            ['GARAGE_1', 'garageredlightboardpin'],
            ['GARAGE_1', 'garagewhitelightboardpin'],
            ['GARAGE_2', 'supervisethisgarage'],
            ['GARAGE_2', 'garageboardpin'],
            ['GARAGE_2', 'garagesensorsboardpin'],
            ['GARAGE_3', 'supervisethisgarage'],
            ['GARAGE_3', 'garageboardpin'],
            ['GARAGE_3', 'garagesensorsboardpin'],
            ['ALERT', 'timebetweenalerts'],
            ['NOTIFICATION_COMMON', 'notificationenabled'],
            ['NOTIFICATION_COMMON', 'default_language'],
            ['EMAIL_ACCOUNT_INFORMATION', 'smtp_server'],
            ['EMAIL_ACCOUNT_INFORMATION', 'user'],
            ['EMAIL_ACCOUNT_INFORMATION', 'email_sender_name'],
            ['EMAIL_ACCOUNT_INFORMATION', 'password'],
            ['EMAIL_ACCOUNT_INFORMATION', 'recipientlist'],
            ['NOTIFICATION_MANAGER', 'notification_manager_loop_timeout'],
            ['NOTIFICATION_MANAGER', 'notification_alert_severity_filter'],
            ['USERS', 'garage_admin'],
            ['USERS', 'garage_users'],
            ['INTERNAL', 'config_file_rev'],
            ['INTERNAL', 'alert_definition_file']
        ]

        try:
            for cfg in configParamsUsedinCodeArray:
                  section=cfg[0]
                  param=cfg[1]
                  logstr="Check %s %s" % (section,param)
                  self.getConfigParam(section,param)
                  log.debug(logstr)
        except Exception:
            traceback.print_exc()
            logstr = "Error %s %s NOT defined !" % (section, param)
            log.error(logstr)
            os._exit(-1)


