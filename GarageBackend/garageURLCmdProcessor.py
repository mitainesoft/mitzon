import logging
import logging.handlers
import logging.config
import sys, traceback
import cherrypy
# try:
from cheroot.wsgi import Server as WSGIServer
# except ImportError:
#from cherrypy.wsgiserver import CherryPyWSGIServer as WSGIServer

from GarageBackend.Sensor import Sensor
from GarageBackend.Constants import *
from GarageBackend.CommandQResponse import *
from GarageBackend.ConfigManager import ConfigManager
from GarageBackend.GarageDoor import GarageDoor
from GarageBackend.AlertManager import AlertManager
from GarageBackend.DeviceManager import DeviceManager
from GarageBackend.GarageManager import GarageManager
from GarageBackend.NotificationManager import NotificationManager
from queue import *
from threading import Thread
from GarageBackend.SingletonMeta import SingletonMeta
import types
from time import sleep
import time
import datetime


log = logging.getLogger('garageCmdProcessor')

garage_manager_handler = None #GarageManager()
notification_manager_handler = None

@cherrypy.expose
class garageURLCmdProcessor(metaclass=SingletonMeta):
    def __init__(self, dispatch: Queue):
        log.debug("init garageURLCmdProcessor...")
        #self.deviceList = {}
        self.dispatch = dispatch
        # Read Building Config
        '''Create new device hanlder and connect to USB port for arduino'''

        self.config_handler = ConfigManager()
        self.config_handler.setConfigFileName("config/garage_backend.config")
        self.dev_manager_handler = DeviceManager()
        self.alert_manager_handler = AlertManager()

    @cherrypy.tools.accept(media='text/plain')
    # s.post('http://127.0.0.1:8080/garage/open/g0')
    def _cp_dispatch(self, vpath):
        try:
            debugstr = ("Received vpath=%s len=%d" % (vpath, len(vpath)))
            log.debug(debugstr)
            if len(vpath) == 1:
                cherrypy.request.params['mything'] = vpath.pop()  # ex: garage_door
                return self

            if len(vpath) == 3:
                cherrypy.request.params['mything'] = vpath.pop(0)  # /myid/
                cherrypy.request.params['myservice'] = vpath.pop(0)  # ex: open close
                cherrypy.request.params['myid'] = vpath.pop(0)  # which one 0, 1, 2...
                return self
        except Exception:
            log.error("_cp_dispatch error in garageURL...")
            traceback.print_exc()
            os._exit(-1)


        return vpath

    # @cherrypy.expose
    def GET(self):
        log.info("Garage Request Received GET")
        return cherrypy.session['mything']

    @cherrypy.popargs('myservice')
    @cherrypy.popargs('myid')
    # @cherrypy.expose
    def POST(self, mything, myservice=None, myid=None):
        cherrypy.session['mything'] = mything
        cherrypy.session['myservice'] = myservice
        cherrypy.session['myid'] = myid
        cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
        cherrypy.response.headers["Allow"] = "POST, GET, OPTIONS, DELETE, PUT, PATCH"

        caller = cherrypy.request.remote.ip

        logbuf = "GarageBackend Request Received POST: %s %s %s " % (mything, myservice, myid)
        log.debug(logbuf)

        ## Test Arduino Device
        # self.dispatch.put(('testConnection',"msg Hard coded pin"))

        ## Send all html POST commands to device through device manager
        self.dispatch.put(('processDeviceCommand', mything, myservice, myid))

        resp_str=""

        for sub_nbr in range(0,1): #  1 only DeviceManager 2 Subscribers are DeviceManager and Alert Manager
            try:
                resp=response_queue.get(True, float(self.config_handler.getConfigParam("THREAD_CONTROL","RESP_TIMEOUT")))
                resp_str = resp_str +  resp.getRspPropsToString()
            except Empty:
                resp_str=resp_str + ("RESP_TIMEOUT=%s/%s/%s" %(mything, myservice, myid))

        resp_str += self.alert_manager_handler.status().getRspPropsToString()

        if log.isEnabledFor(logging.DEBUG):
            self.dev_manager_handler.listDevices()
        return resp_str

    # @cherrypy.expose
    def PUT(self):
        cherrypy.session['myservice'] = self.myservice
        logbuf = "Garage Request Received PUT:"
        log.info(logbuf)
        DeviceManager.listDevices(self.deviceList)

    # @cherrypy.expose
    def DELETE(self):
        cherrypy.session.pop('myservice', None)



''' Outside Class'''


# @cherrypy.expose
def command_queue_fn(q: Queue, r: Queue):
    next = q.get()
    while next is not None:
        # log.info(next[0] +'/' + next[1:])
        resp=next[0](*(next[1:]))
        if log.isEnabledFor(logging.DEBUG):
            log.debug("command_queue_fn isinstance next = %s", next[0].__self__.__class__.__name__)
        if next[0].__self__.__class__.__name__ == "DeviceManager":
            r.put(resp)
        else:
            if log.isEnabledFor(logging.DEBUG):
                log.debug("command_queue_fn NOT ADDED TO QUEUE isinstance next = %s", next[0].__self__.__class__.__name__)
            # r.put(CommmandQResponse(0,next[0].__self__.__class__.__name__))
        # if hasattr(next[0], '__self__') and isinstance(next[0].__self__, DeviceManager):
        #     r.put(resp)
        next = q.get()

# @cherrypy.expose
def dispatcher_fn(dispatch: Queue, command: Queue, subscribers: list):
    next = dispatch.get()
    while next is not None:
        name = next[0]
        args = next[1:]
        # log.info('dispatcher_fn name=' + getattr(sub, str(name)) + '  args=' + list(args) )
        for sub in subscribers:
            try:
                #log.debug('dispatcher_fn name= ' + name + 'args=' + args[0] )
                command.put(([getattr(sub, str(name))] + list(args)))
            except AttributeError as exc:
                log.error("dispatcher_fn fn:'%s' arg:'%s'" % (name, args[0]))
                log.error(traceback.extract_statck())
                pass
        next = dispatch.get()




if __name__ == '__main__':

    """
    References:
    [LUH] https://www.owasp.org/index.php/List_of_useful_HTTP_headers
    [XFO] https://www.owasp.org/index.php/Clickjacking_Defense_Cheat_Sheet
    [CSP] https://www.owasp.org/index.php/XSS_(Cross_Site_Scripting)_Prevention_Cheat_Sheet#Bonus_Rule_.232:_Implement_Content_Security_Policy
    """
    _csp_sources = ['default', 'script', 'style', 'img', 'connect', 'font', 'object', 'media', 'frame']
    _csp_default_source = "'self'"
    _csp_rules = list()
    for c in _csp_sources:
        _csp_rules.append('{:s}-src {:s}'.format(c, _csp_default_source))
    _csp = '; '.join(_csp_rules)


    ''' @TODO Hardcoded RotatingFileHandler '''
    logrotate_handler=logging.handlers.RotatingFileHandler("log/garage.log",maxBytes=10485760,backupCount=20,encoding=None, delay=0)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logrotate_handler,
                                  logging.StreamHandler()])

    logrotate_handler.doRollover() #Roolover logs on startup

    server_config = {
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 8050,
            'server.ssl_module': 'builtin',
            #'server.ssl_module': 'pyopenssl',
            'server.ssl_certificate': '/opt/mitainesoft/security/mitainesoftsvr.cert.pem',
            'server.ssl_private_key': '/opt/mitainesoft/security/mitainesoftsvr.key.pem',
            'tools.response_headers.on': False,
            'tools.response_headers.headers': [('Content-Type', 'text/plain'),
                                               ('Strict-Transport-Security', 'max-age=31536000'),
                                               ('X-Frame-Options', 'DENY'),  # [XFO]
                                               ('X-XSS-Protection', '1; mode=block'),  # [LUH]
                                               ('Content-Security-Policy', _csp),  # [CSP]
                                               ('X-Content-Security-Policy', _csp),  # [CSP]
                                               ('X-Webkit-CSP', _csp),  # [CSP]
                                               ('X-Content-Type-Options', 'nosniff')  # [LUH]
                                               ],
            'tools.sessions.secure': True,
            'tools.request_headers.on': False,
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "log",
            # 'log.access_file': 'log/garage_cherrypy_access.log',
            # 'log.error_file': 'log/garage_cherrypy_error.log',
            # 'log.screen': True,
            # 'tools.sessions.on': True,
            'engine.autoreload_on': False,
    }


    garage_backend_conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': False,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        }
    }
    log = logging.getLogger('garageCmdProcessor')


    LOG_CONF = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'void': {
                'format': ''
            },
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
         'handlers': {
           'cherrypy_console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'void',
                'stream': 'ext://sys.stdout'
            },
            'cherrypy_access': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'void',
                'filename': 'log/garage_cherrypy_access.log',
                'maxBytes': 10485760,
                'backupCount': 10,
                'encoding': 'utf8'
            },
            'cherrypy_error': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'void',
                'filename': 'log/garage_cherrypy_error.log',
                'maxBytes': 10485760,
                'backupCount': 10,
                'encoding': 'utf8'
            },
        },
        'loggers': {
            # # Only Log Request and reponses to file.  Screen is the next block!
            'cherrypy.access': {
                'handlers': ['cherrypy_access'],
                'level': 'INFO',
                'propagate': False
            },
            # # Log Requests to screen
            # 'cherrypy.access': {
            #     'handlers': ['cherrypy_console', 'cherrypy_access'],
            #     'level': 'INFO',
            #     'propagate': False
            # },
            'cherrypy.error': {
                'handlers': ['cherrypy_console', 'cherrypy_error'],
                'level': 'INFO',
                'propagate': False
            },
        }
    }

    logging.config.dictConfig(LOG_CONF)



    log.setLevel(logging.INFO)
    log.info("Starting garage...")


    '''Subscriber - Dispatcher '''
    command_queue = Queue()
    response_queue = Queue()
    dispatch_queue = Queue()

    my_garageURLCmdProcessor = garageURLCmdProcessor(dispatch_queue)

    # pub1 = Pub1(dispatch_queue)
    sub1 = DeviceManager()
    sub2 = AlertManager()

    thread_command_queue = Thread(target=command_queue_fn, name='cmd_queue', args=(command_queue,response_queue,))
    thread_dispatcher = Thread(target=dispatcher_fn, name='dispath_queue',
                               args=(dispatch_queue, command_queue, [sub1, sub2]))

    garage_manager_handler = GarageManager()
    thread_garage_manager = Thread(target=GarageManager.monitor,
                                   args=(garage_manager_handler,), name='garage_manager',
                                   daemon=True)

    notification_manager_handler = NotificationManager()
    thread_notification_manager = Thread(target=NotificationManager.processnotif,
                                   args=(notification_manager_handler,), name='notification_manager',
                                   daemon=True)

    thread_command_queue.start()
    thread_dispatcher.start()
    thread_garage_manager.start()
    thread_notification_manager.start()
    try:
        cherrypy.config.update(server_config)

        # cherrypy.quickstart(my_garageURLCmdProcessor,'/',garage_backend_conf)
        #cherrypy.quickstart(RootServer())

        #cherrypy.quickstart(my_garageURLCmdProcessor)

        #cherrypy.tree.mount(garageURLCmdProcessor(dispatch_queue), script_name='/', config=server_config4)
        cherrypy.quickstart(my_garageURLCmdProcessor, '/',garage_backend_conf)

    except Exception:
        log.error("Cherrypy quickstart fail !")
        traceback.print_exc()
        os._exit(-1)



    # cherrypy.tree.mount(my_garageURLCmdProcessor, '/backend', garage_backend_conf)
    # cherrypy.engine.start()
    # cherrypy.engine.block()

    dispatch_queue.put(None)
    command_queue.put(None)

    # thread_command_queue.join(THREAD_TIMEOUTS)
    # thread_dispatcher.join(THREAD_TIMEOUTS)
    # thread_garage_manager.join(THREAD_TIMEOUTS)

    cherrypy.engine.exit()
    os._exit(0)

