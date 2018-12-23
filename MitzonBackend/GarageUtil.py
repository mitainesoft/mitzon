import logging
import time
import datetime
import cherrypy
import os, sys, traceback

log = logging.getLogger('Garage.GarageUtil')

class GarageUtil():

    def __init__(self):
        pass

    def getTimePrintOut(self, millisnbr):
        tmpbuf = ""

        #
        #          /* 4 is mininum width, 2 is precision float value is copied onto str_temp*/
        # dtostrf(_timeLeftMin, 6, 2, strbuf)

        tmpmillins = int(millisnbr)
        tmphours = int(millisnbr / 3600)
        tmphours_remain = millisnbr % 3600
        tmpmillins = int(tmpmillins - (tmphours * 3600))

        tmpmin = int(tmpmillins / 60)
        tmpmin_remain = tmpmillins % 60
        tmpmillins = int(tmpmillins - (tmpmin * 60))

        tmpsec = int(tmpmillins / 1)
        tmpsec_remain = tmpmillins % 1
        tmpmillins = int(tmpmillins - (tmpsec * 1))

        if (tmphours > 0):
            tmpbuf = tmpbuf + str(tmphours) + "h"

        if (tmpmin > 0):
            tmpbuf = tmpbuf + str(tmpmin) + "m"

        if (tmpsec > 0 and tmpmin < 3 and tmphours == 0):
            tmpbuf = tmpbuf + str(tmpsec) + "s"

        return tmpbuf



