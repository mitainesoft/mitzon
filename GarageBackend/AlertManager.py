import logging
from GarageBackend.Constants import *
from GarageBackend.CommandQResponse import *


log = logging.getLogger('garageCmdProcessor')


class AlertManager():
    s_id = -1
    s_status = G_UNKNOWN
    s_board_pin = 7
    s_name="[UNKNOWN]"

    def __init__(self):
        log.info("AlertManager started...")
        pass

    #required for subcriber
    def processDeviceCommand(self, mything, myservice, myid):
        # log.info(str(self.deviceList))
        logbuf = "AlertManager Cmd Received: %s/%s/%s " % (mything, myservice, myid)
        log.info(logbuf)
        resp = CommmandQResponse(0,"processDeviceCommand AlertManager called %s/%s/%s " % (mything, myservice, myid))
        return (resp)

    def enableSiren(self,mything,myservice,myid):
        isgarageopen= True
        return isgarageopen

    def test(self):

        return CommmandQResponse(0, "test AlertManager")

    def status(self):
        log.debug("AlertManager status called !")

        resp = CommmandQResponse(0,"status AlertManager" )
        return (resp)