""" Read Building definifion from file"""
import logging
from GarageBackend.Constants import *
import configparser
from GarageBackend.SingletonMeta import SingletonMeta
import traceback
import sys

log = logging.getLogger('ConfigManager')

class ConfigManager(metaclass=SingletonMeta):

    def __init__(self):
        log.debug("Started...")
        self.configfilename="config/garage_backend.config"

        # Legacy Value to get rif of !
        self.RESP_TIMEOUT = 10
        self.GARAGE_MANAGER_LOOP_TIMEOUT = 5
        self.GARAGE_MANAGER_MAX_FAILURE = 3
        self.DefaultTestPin = 7

        self.NBR_GARAGE=2

        self.GARAGE_BOARD_PIN = [7, 6, 5, 4]

        ''' 2 sensor on top config '''
        self.GARAGE_SENSORS_PIN = [[8, 9],
                              [10, 11],
                              [8, 9],  # invalid !
                              [10, 11]  # invalid !
                              ]

        self.GARAGE_NAME = ["GARAGE_0", "GARAGE_1", "GARAGE_2", "GARAGE_3"]

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
            sys.exit(-1)
        try:
            config = configparser.ConfigParser()
            config.read(self.configfilename)
            for key in config['GARAGE_0']:
                log.info(key)
            pass
        except KeyError:
            log.info("Something went wrong while reading the config, Suspect is wrong file name or param")
            traceback.print_exc()
            sys.exit(-1)
        except Exception:
            log.info("Something went wrong while reading the config, Suspect is wrong file name")
            traceback.print_exc()
            sys.exit(-1)
            pass

    def getConfigParam(self,param):
        return 7
