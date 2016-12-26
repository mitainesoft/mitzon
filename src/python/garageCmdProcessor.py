import cherrypy
import sys
import logging
from src.python.Constants import *
from src.python.DeviceManager import DeviceManager
from src.python.ReadBuildingConfig import *

log = logging.getLogger(__name__)


@cherrypy.expose
class DeviceControllerWebService():
    mything="THING1"
    myservice="SERV1"
    myid="ID1"   
    def __init__(self):

        #Read Building Config
        self.mydevice = Device()
        self.connecthandler = DeviceManager()
        pin=0
        while (pin <  NBR_GARAGE ):
            logging.info('Initialize board pin %d' % GARAGE_BOARDPIN[pin])
            self.connecthandler.initBoardPinMode(GARAGE_BOARDPIN[pin])
            pin = pin + 1
        log.info ("init DeviceControllerWebService stuff")
    @cherrypy.tools.accept(media='text/plain')    

	# s.post('http://127.0.0.1:8080/garage/open/g0')
    def _cp_dispatch(self, vpath):
        #print ("JLC vpath=", vpath , "len=" , len(vpath))
        debugstr= ("JLC vpath=%s len=%d" % (vpath,len(vpath)) )
        log.info(debugstr)
        if len(vpath) == 1:
            cherrypy.request.params['mything'] = vpath.pop() # ex: garage_door
            return self        
            
        if len(vpath) == 3:
            cherrypy.request.params['mything'] = vpath.pop(0) # /myid/
            cherrypy.request.params['myservice'] = vpath.pop(0)  # ex: open close
            cherrypy.request.params['myid'] = vpath.pop(0) # which one 0, 1, 2...
            return self
            
        return vpath
        
    def GET(self):
        log.info("Garage Request Received GET")
        return cherrypy.session['mything']

    @cherrypy.popargs('myservice')
    @cherrypy.popargs('myid')
    def POST(self, mything, myservice=None,myid=None):
        cherrypy.session['mything'] = mything
        cherrypy.session['myservice'] = myservice
        cherrypy.session['myid'] = myid
        logbuf="Garage Request Received POST: %s %s %s " % (mything,myservice,myid)
        log.info ( logbuf )

        self.connecthandler.testConnection()


        return mything

    def PUT(self):
        cherrypy.session['myservice'] = self.myservice
        logbuf="Garage Request Received PUT: %s %s %s " % (mything,myservice,myid)
        log.info ( logbuf )

    def DELETE(self):
        cherrypy.session.pop('myservice', None)
    

class Device():
    @cherrypy.expose
    def index(self):
        return 'About (%s) %s by %s...' % (mything, myid, myservice )

if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': False,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        }
    }
    cherrypy.config.update ({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 8080,
                             'tools.staticdir.on': True,
                             'tools.response_headers.on': False,
                             'tools.request_headers.on': False,
                             'tools.staticdir.dir': ".",
                             'log.access_file': "garage_cherrypy_access.log",
                             'log.error_file': "garage_cherrypy_error.log",
                             'log.screen': False,
                             'tools.sessions.on': True,
                            })


    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    log.setLevel(logging.INFO)

    log.info("Rapberry Arduino connection Started...")

    cherrypy.quickstart(DeviceControllerWebService(), '/', conf)
    #System out here ! code not run.



    