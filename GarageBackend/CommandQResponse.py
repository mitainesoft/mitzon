from GarageBackend.Constants import *
from GarageBackend.ConfigManager import *
import time
import datetime
import json

class CommmandQResponse():
    def __init__(self,cmdid,module,device, status,rsptxt):
        #tid = tramsaction id. Currently based on time !
        self.tid=cmdid
        self.module=module
        self.device=device
        self.status=status
        self.text=rsptxt
        # self.config_handler = ConfigManager()


    def updateRspProps(self,cmdid,module,device, status,rsptxt):

        self.tid=cmdid
        self.module=module
        self.device=device
        self.status=status
        self.text=rsptxt
        pass

    def getRspPropsToString(self):
        #Format according to module type i.e. DeviceManager or AlertManage to keep backward compatibility
        if (self.module=="[DeviceManager]"):
            retstr = "tid:%020d %s %s:%s" % (self.tid, self.module, self.device, self.status)
            pass
        elif (self.module=="[AlertManager]"):
            retstr = "tid:%020d %s %s" % (self.tid, self.module,self.text)
        else:
            retstr="tid:%020d %s%s%s%s" %(self.tid,self.module,self.device,self.status,self.text)

        return (retstr)

    def getRspPropsToArray(self):
        return ([self.tid,self.module,self.device,self.status,self.text])
        pass
