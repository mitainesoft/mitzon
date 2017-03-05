from GarageBackend.Constants import *
from GarageBackend.ReadBuildingConfig import *

class CommmandQResponse():
    def __init__(self,cmdid,rsptxt):
        self.id=cmdid
        self.text=rsptxt
        pass

    def updateRspProps(self,cmdid,text):
        self.id=cmdid
        self.text=text
        pass

    def getRspPropsToString(self):
        return ("id:%020d %s " %(self.id,self.text))
