import logging
from GarageBackend.Constants import *


log = logging.getLogger(__name__)

class Siren():
    s_id = -1
    s_status = G_UNKNOWN
    s_board_pin = 7
    s_name="[UNKNOWN]"

    def __init__(self):
        pass

    def enableSiren(self,mything,myservice,myid):
        isgarageopen= True
        return isgarageopen