import logging
import sys, traceback
import cherrypy
from GarageBackend.Sensor import Sensor
from GarageBackend.Constants import *
from GarageBackend.CommandQResponse import *
from GarageBackend.ReadBuildingConfig import *
from GarageBackend.GarageDoor import GarageDoor
from GarageBackend.AlertManager import AlertManager
from GarageBackend.DeviceManager import DeviceManager
from GarageBackend.GarageManager import GarageManager
from queue import *
from threading import Thread
from GarageBackend.SingletonMeta import SingletonMeta
import types
from cherrypy.lib import httputil, file_generator

log = logging.getLogger('garageCmdProcessor')

garage_manager_handler = GarageManager()

@cherrypy.expose
class garageURLCmdProcessor(metaclass=SingletonMeta):
    def __init__(self, dispatch: Queue):

        log.info("init garageURLCmdProcessor...")
        self.deviceList = {}
        self.dispatch = dispatch
        # Read Building Config
        '''Create new device hanlder and connect to USB port for arduino'''
        self.dev_manager_handler = DeviceManager(self.deviceList)
        self.alert_manager_handler = AlertManager()


    @cherrypy.tools.accept(media='text/plain')
    # s.post('http://127.0.0.1:8080/garage/open/g0')
    def _cp_dispatch(self, vpath):
        # print ("JLC vpath=", vpath , "len=" , len(vpath))
        debugstr = ("JLC vpath=%s len=%d" % (vpath, len(vpath)))
        log.debug(debugstr)
        if len(vpath) == 1:
            cherrypy.request.params['mything'] = vpath.pop()  # ex: garage_door
            return self

        if len(vpath) == 3:
            cherrypy.request.params['mything'] = vpath.pop(0)  # /myid/
            cherrypy.request.params['myservice'] = vpath.pop(0)  # ex: open close
            cherrypy.request.params['myid'] = vpath.pop(0)  # which one 0, 1, 2...
            return self

        return vpath


    def GET(self):
        log.info("Garage Request Received GET")
        return cherrypy.session['mything']

    @cherrypy.popargs('myservice')
    @cherrypy.popargs('myid')
    def POST(self, mything, myservice=None, myid=None):
        cherrypy.session['mything'] = mything
        cherrypy.session['myservice'] = myservice
        cherrypy.session['myid'] = myid
        logbuf = "GarageBackend Request Received POST: %s %s %s " % (mything, myservice, myid)
        log.info(logbuf)

        ## Test Arduino Device
        # self.dispatch.put(('testConnection',"msg Hard coded pin"))

        ## Send all html POST commands to device through device manager
        self.dispatch.put(('processDeviceCommand', mything, myservice, myid))

        resp_str=""

        for sub_nbr in range(0,2): #Subscribers are DeviceManager and Alert Manager
            try:
                resp=response_queue.get(True, RESP_TIMEOUT)
                resp_str = resp_str +  resp.getRspPropsToString()
            except Empty:
                resp_str=resp_str + ("RESP_TIMEOUT=%s/%s/%s" %(mything, myservice, myid))

        DeviceManager.listDevices(self,self.deviceList)
        return resp_str


    def PUT(self):
        cherrypy.session['myservice'] = self.myservice
        logbuf = "Garage Request Received PUT:"
        log.info(logbuf)
        DeviceManager.listDevices(self.deviceList)


    def DELETE(self):
        cherrypy.session.pop('myservice', None)


''' Outside Class'''



def command_queue_fn(q: Queue, r: Queue):
    next = q.get()
    while next is not None:
        # log.info(next[0] +'/' + next[1:])
        resp=next[0](*(next[1:]))
        log.debug("isinstance next = %s", next[0].__self__.__class__.__name__)
        r.put(resp)
        # if hasattr(next[0], '__self__') and isinstance(next[0].__self__, DeviceManager):
        #     r.put(resp)
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
            except AttributeError as exc:
                log.error("dispatcher_fn fn:'%s' arg:'%s'" % (name, args[0]))
                log.error(traceback.extract_statck())
                pass
        next = dispatch.get()




# class Device():
#     @cherrypy.expose
#     def index(self):
#         return 'About (%s) %s by %s...' % (mything, myid, myservice )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler("log/garage.log"),
                                  logging.StreamHandler()])

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': False,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 8080,
                            'tools.staticdir.on': True,
                            'tools.response_headers.on': False,
                            'tools.request_headers.on': False,
                            'tools.staticdir.dir': "log",
                            'log.access_file': "log/garage_cherrypy_access.log",
                            'log.error_file': "log/garage_cherrypy_error.log",
                            'log.screen': False,
                            'tools.sessions.on': True,
                            'engine.autoreload_on': False,
                            })


    log.setLevel(logging.DEBUG)

    log.info("Starting garage...")



    '''Subscriber - Dispatcher '''
    command_queue = Queue()
    response_queue = Queue()
    dispatch_queue = Queue()

    my_garageURLCmdProcessor = garageURLCmdProcessor(dispatch_queue)

    # pub1 = Pub1(dispatch_queue)
    sub1 = DeviceManager({})
    sub2 = AlertManager()

    thread_command_queue = Thread(target=command_queue_fn, name='cmd_queue', args=(command_queue,response_queue,))
    thread_dispatcher = Thread(target=dispatcher_fn, name='dispath_queue',
                               args=(dispatch_queue, command_queue, [sub1, sub2]))

    thread_garage_manager = Thread(target=GarageManager.monitor,
                                   args=(garage_manager_handler, my_garageURLCmdProcessor.deviceList), name='garage_manager',
                                   daemon=True)
    thread_garage_manager.start()
    # thread_garage_manager = Thread(target=GarageManager.monitor, args=(garage_manager_handler,device_manager_handler), name='garage_manager', daemon=True)


    thread_command_queue.start()
    thread_dispatcher.start()
    # thread_garage_manager.start()

    # pub1.cmdloop()



    cherrypy.quickstart(my_garageURLCmdProcessor, '/', conf)
    # System out here ! code not run.


    dispatch_queue.put(None)
    command_queue.put(None)

    thread_command_queue.join(THREAD_TIMEOUTS)
    thread_dispatcher.join(THREAD_TIMEOUTS)
    # thread_garage_manager.join(THREAD_TIMEOUTS)

    cherrypy.engine.exit()
    exit(0)

