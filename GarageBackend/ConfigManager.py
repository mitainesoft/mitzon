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

        # Legacy Value to get rif of !

        # self.DefaultTestPin = 7
        self.configSections = []
        self.NBR_GARAGE=0 #Calculated value

        self.GARAGE_BOARD_PIN = [7, 6, 5, 4]

        ''' 2 sensor on top config '''
        self.GARAGE_SENSORS_PIN = [[8, 9],
                              [10, 11],
                              [8, 9],  # invalid !
                              [10, 11]  # invalid !
                              ]

        self.GARAGE_NAME = [] # ["GARAGE_0", "GARAGE_1", "GARAGE_2", "GARAGE_3"]

        pass

    def setConfigFileName(self,filename):
        log.info("Set config file name...")
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
                        log.info("config file, not garage: " + keySections + "...Skipping" )
                for key in self.config[keySections]:
                    log.info(keySections + "/" + key + " = " + self.config[keySections][key])

            pass
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
            log.info("Section:"+section+" param:" + param +" Not exist! Die !!!")
            traceback.print_exc()
            os._exit(-1)
        return val
