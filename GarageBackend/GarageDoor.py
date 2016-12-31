import logging
from GarageBackend.Constants import *
from GarageBackend.ReadBuildingConfig import *
import time
import datetime

log = logging.getLogger(__name__)

class GarageDoor():

    def __init__(self,garage_id):
        self.g_id = garage_id
        self.g_name = GARAGE_NAME[garage_id]
        self.g_board_pin_relay = GARAGE_BOARD_PIN[garage_id]
        self.g_status = G_UNKNOWN
        self.g_sensor_props = {}
        self.modified_time=int(time.time())
        #self.modified=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    def isGarageOpen(self,mything,myservice,myid):
        isgarageopen= True
        return isgarageopen

    def status(self):
        pass

    def addSensor(self, key,sensor_props):
        self.g_sensor_props[key]=sensor_props
        log.info(str(sensor_props))
        pass




