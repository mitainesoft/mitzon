import logging
from GarageBackend.Constants import *
from GarageBackend.CommandQResponse import *
from GarageBackend.SingletonMeta import SingletonMeta
from GarageBackend.CommandQResponse import *
from queue import *



log = logging.getLogger('garageCmdProcessor')


class AlertManager(metaclass=SingletonMeta):


    def __init__(self):
        log.info("AlertManager started...")
        self.s_id = -1
        self.s_status = G_UNKNOWN
        self.s_board_pin = 7
        self.s_name = "[UNKNOWN]"
        self.alertQ = Queue()
        pass

    #required for subcriber
    def processDeviceCommand(self, mything, myservice, myid):
        # log.info(str(self.deviceList))
        logbuf = "AlertManager Cmd Received: %s/%s/%s " % (mything, myservice, myid)
        log.info(logbuf)
        resp = CommmandQResponse(0,"Alert=None")
        return (resp)

    def enableSiren(self,mything,myservice,myid):
        isgarageopen= True
        return isgarageopen

    def addAlert(self, alert: CommmandQResponse):
        self.alertQ.put(alert)
        pass

    def clearAlert(self):
        self.alertQ.empty()
        log.warning("Alert Queue Blindly Cleared (need to improve!!!)!!!")

    def test(self):

        return CommmandQResponse(0, "test AlertManager")

    def status(self):
        log.debug("AlertManager status called !")

        resp = CommmandQResponse(0,"status AlertManager" )
        return (resp)