from GarageBackend.Constants import *
from GarageBackend.ConfigManager import *

class CommmandQResponse():
    def __init__(self,cmdid,rsptxt):
        #tid = tramsaction id. Currently based on time !
        self.tid=cmdid
        self.text=rsptxt
        pass

    def updateRspProps(self,cmdid,text):
        self.tid=cmdid
        self.text=text
        pass

    def getRspPropsToString(self):
        return ("tid:%020d %s " %(self.tid,self.text))
