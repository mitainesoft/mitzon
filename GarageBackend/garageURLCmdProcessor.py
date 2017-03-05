import logging
import sys, traceback
import cherrypy
from GarageBackend.Sensor import Sensor
from GarageBackend.Constants import *
from GarageBackend.CommandQResponse import *
from GarageBackend.ReadBuildingConfig import *
from GarageBackend.GarageDoor import GarageDoor
from GarageBackend.Siren import Siren
from GarageBackend.DeviceManager import DeviceManager
from queue import *
from threading import Thread
from cherrypy.lib import httputil, file_generator


#log = logging.getLogger(__name__)
log = logging.getLogger('garageCmdProcessor')


@cherrypy.expose
class garageURLCmdProcessor():
    def __init__(self, dispatch: Queue):
        self.deviceList = {}
        self.dispatch = dispatch
        # Read Building Config
        '''Create new device hanlder and connect to USB port for arduino'''
        self.dev_manager_handler = DeviceManager(self.deviceList)
        log.info("init DeviceControllerWebService stuff")

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

        try:
            resp=response_queue.get(True,RESP_TIMEOUT)
        except Empty:
            return ("RESP_TIMEOUT %s/%s/%s" %(mything, myservice, myid))


        return resp.getRspPropsToString()




    def PUT(self):
        cherrypy.session['myservice'] = self.myservice
        logbuf = "Garage Request Received PUT:"
        log.info(logbuf)

    def DELETE(self):
        cherrypy.session.pop('myservice', None)


''' Outside Class'''


def command_queue_fn(q: Queue, r: Queue):
    next = q.get()
    while next is not None:
        # log.info(next[0] +'/' + next[1:])
        resp=next[0](*(next[1:]))
        r.put(resp)
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
    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    # create file handler which logs even debug messages
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler('garage.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    log.addHandler(fh)
    log.addHandler(ch)


    cherrypy.log.error_log.addHandler(ch)
    cherrypy.log.access_log.addHandler(fh)


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
                            })



    log.info("Starting garage...")


    '''Subscriber - Dispatcher '''
    command_queue = Queue()
    response_queue = Queue()
    dispatch_queue = Queue()
    # pub1 = Pub1(dispatch_queue)
    sub1 = DeviceManager({})
    #sub2 = Siren()

    thread_command_queue = Thread(target=command_queue_fn, name='cmd_queue', args=(command_queue,response_queue,))
    thread_dispatcher = Thread(target=dispatcher_fn, name='dispath_queue',
                               args=(dispatch_queue, command_queue, [sub1]))

    thread_command_queue.start()
    thread_dispatcher.start()

    # pub1.cmdloop()



    cherrypy.quickstart(garageURLCmdProcessor(dispatch_queue), '/', conf)
    # System out here ! code not run.

    dispatch_queue.put(None)
    command_queue.put(None)

    thread_command_queue.join(3)
    thread_dispatcher.join(3)
