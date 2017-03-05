from GarageBackend.Constants import *
from GarageBackend.ReadBuildingConfig import *

log = logging.getLogger('Sensor')


class Sensor():
    def __init__(self,id,board_pin_id):
        self.id=id
        self.board_pin_id=board_pin_id
        self.status=S_UNKNOWN
        self.digital=True
        pass

    def updateSensorProps(self,status):
        self.status=status
        pass


