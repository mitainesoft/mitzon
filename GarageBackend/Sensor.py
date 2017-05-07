from GarageBackend.Constants import *
from GarageBackend.ConfigManager import *
import datetime
import time

log = logging.getLogger('Sensor')


class Sensor():
    def __init__(self,id,board_pin_id):
        self.id=id
        self.board_pin_id=board_pin_id
        self.status=S_UNKNOWN
        self.digital=True
        self.s_update_time = int(time.time())
        pass

    def updateSensorProps(self,status):
        self.status=status
        self.s_update_time = int(time.time())
        pass


