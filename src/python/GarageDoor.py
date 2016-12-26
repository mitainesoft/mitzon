from src.python.Constants import *
import logging

log = logging.getLogger(__name__)

class GarageDoor():
    g_id = -1
    g_status = G_UNKNOWN
    g_board_pin = 7

    def __init__(self):
        pass

    def isGarageOpen(self,mything,myservice,myid):
        isgarageopen= True
        return isgarageopen

