import logging
import sys
import cherrypy
from GarageBackend.Constants import *
from GarageBackend.ReadBuildingConfig import *
from GarageBackend.GarageDoor import GarageDoor
from GarageBackend.Siren import Siren
from GarageBackend.DeviceManager import DeviceManager
from queue import Queue
from threading import Thread

#log = logging.getLogger(__name__)
log = logging.getLogger('garageCmdProcessor')

@cherrypy.expose
class DeviceControllerWebService():

    def __init__(self, dispatch: Queue):
        self.deviceList = {}
        self.dispatch = dispatch
        #Read Building Config
        # self.mydevice = Device()
        self.connecthandler = DeviceManager()

        # replace by config
        for garage_id in range(NBR_GARAGE):
            logging.info('Initialize board garage_id %d ** Control Board Pin %d' % (garage_id, GARAGE_BOARDPIN[garage_id]))
            self.connecthandler.initBoardPinMode(GARAGE_BOARDPIN[garage_id])
            obj = GarageDoor()
            obj.g_id = garage_id
            obj.g_name = GARAGE_NAME[garage_id]
            obj.g_board_pin = GARAGE_BOARDPIN[garage_id]
            obj_key = "garage_%d" % garage_id
            self.deviceList[obj_key] = obj
            garage_id = garage_id + 1
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
        logbuf="GarageBackend Request Received POST: %s %s %s " % (mything,myservice,myid)
        log.info ( logbuf )

        ## Test Arduino Device
        self.dispatch.put(('testConnection', self.deviceList))

        ## Send all html POST commands to device through device manager
        self.dispatch.put(('processDeviceCommand', mything,myservice,myid, self.deviceList))
        return mything

    def PUT(self):
        cherrypy.session['myservice'] = self.myservice
        logbuf="Garage Request Received PUT:"
        log.info ( logbuf )

    def DELETE(self):
        cherrypy.session.pop('myservice', None)


''' Outside Class'''
def command_queue_fn(q: Queue):
    next = q.get()
    while next is not None:
        # log.info(next[0] +'/' + next[1:])
        next[0](*(next[1:]))
        next = q.get()

def dispatcher_fn(dispatch: Queue, command: Queue, subscribers: list):
    next = dispatch.get()
    while next is not None:
        name = next[0]
        args = next[1:]
        # log.info('dispatcher_fn name=' + getattr(sub, str(name)) + '  args=' + list(args) )
        for sub in subscribers:
            try:
                # log.info('dispatcher_fn name= ' + name + 'args=' + args[0] )
                command.put(([getattr(sub, str(name))] + list(args)))
            except AttributeError:
                log.debug(AttributeError)
                pass
        next = dispatch.get()



# class Device():
#     @cherrypy.expose
#     def index(self):
#         return 'About (%s) %s by %s...' % (mything, myid, myservice )

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
                             'tools.staticdir.dir': "log",
                             'log.access_file': "log/garage_cherrypy_access.log",
                             'log.error_file': "log/garage_cherrypy_error.log",
                             'log.screen': False,
                             'tools.sessions.on': True,
                            })

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    log.setLevel(logging.INFO)
    log.info("Rapberry Arduino connection Started...")

    '''Subscriber - Dispatcher '''
    command_queue = Queue()
    dispatch_queue = Queue()
    #pub1 = Pub1(dispatch_queue)
    sub1 = DeviceManager()
    sub2 = GarageDoor()

    thread_command_queue = Thread(target=command_queue_fn, name='cmd_queue', args=(command_queue,))
    thread_dispatcher = Thread(target=dispatcher_fn, name='dispath_queue', args=(dispatch_queue, command_queue, [sub1, sub2]))

    thread_command_queue.start()
    thread_dispatcher.start()

    # pub1.cmdloop()



    cherrypy.quickstart(DeviceControllerWebService(dispatch_queue), '/', conf)
    #System out here ! code not run.

    dispatch_queue.put(None)
    command_queue.put(None)

    thread_command_queue.join(3)
    thread_dispatcher.join(3)


    