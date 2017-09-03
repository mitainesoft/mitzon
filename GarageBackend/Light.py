from GarageBackend.Constants import *
from GarageBackend.ConfigManager import *
import datetime
import time

log = logging.getLogger('Light')


class Light():
    def __init__(self,id,board_pin_id):
        self.s_update_time = time.time()
        pass

    def updateLightProps(self,status):
        self.s_update_time = time.time()
        pass

