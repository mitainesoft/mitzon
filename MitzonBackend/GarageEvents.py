import logging
from MitzonBackend.Constants import *
from MitzonBackend.ConfigManager import *
from MitzonBackend.CommandQResponse import *
from nanpy import ArduinoApi, SerialManager

from time import sleep
import time
import datetime

log = logging.getLogger('GarageEvents')

class GarageManager():

    def __init__(self):
        log.info("GarageEvents Starting")




