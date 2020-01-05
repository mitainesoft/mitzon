import logging
import logging.handlers
import logging.config
import sys, traceback
import cherrypy
# try:
from cheroot.wsgi import Server as WSGIServer
# except ImportError:
#from cherrypy.wsgiserver import CherryPyWSGIServer as WSGIServer

from MitzonBackend.Sensor import Sensor
from MitzonBackend.Constants import *
from MitzonBackend.CommandQResponse import *
from MitzonBackend.ConfigManager import ConfigManager
from MitzonBackend.GarageDoor import GarageDoor
from MitzonBackend.AlertManager import AlertManager
from MitzonBackend.DeviceManager import DeviceManager
from MitzonBackend.GarageManager import GarageManager
from MitzonBackend.ValveManager import ValveManager
from MitzonBackend.NotificationManager import NotificationManager
from queue import *
from threading import Thread
from MitzonBackend.SingletonMeta import SingletonMeta
import types
from time import sleep
import time
import datetime
import json

log = logging.getLogger('Garage.mitzonURLCmdProcessor')

garage_manager_handler = None #GarageManager()
valve_manager_handler = None #ValveManager()

notification_manager_handler = None

@cherrypy.expose
class mitzonURLCmdProcessor(metaclass=SingletonMeta):
    def __init__(self, dispatch: Queue):
        log.debug("init mitzonURLCmdProcessor...")
        #self.deviceList = {}
        self.dispatch = dispatch
        # Read Building Config
        '''Create new device hanlder and connect to USB port for arduino'''

        self.config_handler = ConfigManager()
        self.config_handler.setConfigFileName("config/mitzon_backend.config")
        self.dev_manager_handler = DeviceManager()
        self.alert_manager_handler = AlertManager()

        self.NBR_QUEUE=2
        self.server_socket_host =self.config_handler.getConfigParam("SECURITY", "SERVER_SOCKET_HOST")
        self.server_socket_port = int(self.config_handler.getConfigParam("SECURITY", "SERVER_SOCKET_PORT"))
        self.server_ssl_module = self.config_handler.getConfigParam("SECURITY", "SERVER_SSL_MODULE")
        self.server_ssl_certificate = self.config_handler.getConfigParam("SECURITY", "SERVER_SSL_CERTIFICATE")
        self.server_ssl_private_key = self.config_handler.getConfigParam("SECURITY", "SERVER_SSL_PRIVATE_KEY")


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

        logbuf = "MitzonBackend Request Received POST: %s %s %s " % (mything, myservice, myid)
        log.debug(logbuf)

        ## Test Arduino Device
        # self.dispatch.put(('testConnection',"msg Hard coded pin"))

        ## Send all html POST commands to device through device manager
        self.dispatch.put(('processDeviceCommand', mything, myservice, myid))

        resp_str=""
        resp_array = {}
        sub_nbr=0

        loopstarttime=time.time()
        # for sub_nbr in range(0,2): #  1 only DeviceManager 2 Subscribers are DeviceManager and Alert Manager. Not
        while response_queue.qsize()>0 or ( sub_nbr<self.NBR_QUEUE and (time.time()<(loopstarttime+float(self.config_handler.getConfigParam("THREAD_CONTROL","RESP_TIMEOUT")))) ):
            try:
                resp=response_queue.get(True, float(self.config_handler.getConfigParam("THREAD_CONTROL","RESP_TIMEOUT")))
                resp_str = resp_str +  resp.getRspPropsToString()+" "
                resp_array[sub_nbr]=resp.getRspPropsToArray()
                sub_nbr+=1
            except Empty:
                log.error("response_queue RESP_TIMEOUT=%s/%s/%s" %(mything, myservice, myid))
                # resp_str=resp_str + ("RESP_TIMEOUT=%s/%s/%s" %(mything, myservice, myid))

        resp_str=resp_str[:-1]  #remove Trailing space
        # resp_str += self.alert_manager_handler.status().getRspPropsToString()

        if log.isEnabledFor(logging.DEBUG):
            self.dev_manager_handler.listDevices()

        resp_json=json.dumps(resp_array)

        # Uncomment return statement below.
        return resp_json
        #return resp_str


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
        elif next[0].__self__.__class__.__name__ == "AlertManager":
            r.put(resp)
            if log.isEnabledFor(logging.DEBUG):
                # log.debug("command_queue_fn NOT ADDED TO QUEUE isinstance next = %s",
                log.debug("command_queue_fn ADDED TO QUEUE isinstance next = %s",
                           next[0].__self__.__class__.__name__)
        else:
            log.error("Unknown class %s" % (next[0].__self__.__class__.__name__))
            traceback.print_exc()
            os._exit(-1)

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

    dispatch_queue = Queue()
    garageHandler = mitzonURLCmdProcessor(dispatch_queue)


    # ''' @TODO Hardcoded RotatingFileHandler '''
    # logrotate_handler=logging.handlers.RotatingFileHandler("log/mitzon.log",maxBytes=10485760,backupCount=20,encoding=None, delay=0)
    # logging.basicConfig(level=logging.INFO,
    #                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #                     handlers=[logrotate_handler,
    #                               logging.StreamHandler()])
    #
    # logrotate_handler.doRollover() #Roolover logs on startup

    server_config = {
            'server.socket_host': garageHandler.server_socket_host,
            'server.socket_port': garageHandler.server_socket_port,
            'server.ssl_module': garageHandler.server_ssl_module,
            #'server.ssl_module': 'pyopenssl',
            'server.ssl_certificate': garageHandler.server_ssl_certificate,
            'server.ssl_private_key': garageHandler.server_ssl_private_key,
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
             'Garage': { #{"log/mitzon.log", maxBytes=, backupCount=20, encoding=None,delay=0, logging.handlers.RotatingFileHandler
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Garage.FileHandler"),
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'filename': 'log/mitzon.log',
                'maxBytes': 104857600,
                'backupCount': 20,
                'encoding': 'utf8'
            },
           'cherrypy_console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'cherrypy_access': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'filename': 'log/garage_cherrypy_access.log',
                'maxBytes': 10485760,
                'backupCount': 10,
                'encoding': 'utf8'
            },
            'cherrypy_error': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'filename': 'log/garage_cherrypy_error.log',
                'maxBytes': 10485760,
                'backupCount': 10,
                'encoding': 'utf8'
            },
        },
        'loggers': {
            'Garage.AlertManager': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Garage.AlertManager"),
                'propagate': True
            },
            'Garage.ConfigManager': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Garage.ConfigManager"),
                'propagate': True
            },
            'Garage.DeviceManager': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Garage.DeviceManager"),
                'propagate': True
            },
            'Garage.GarageDoor': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Garage.GarageDoor"),
                'propagate': True
            },
            'Garage.GarageManager': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Garage.GarageManager"),
                'propagate': True
            },
            'Valve.Valve': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Valve.Valve"),
                'propagate': True
            },
            'Valve.ValveManager': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Valve.ValveManager"),
                'propagate': True
            },

            'Garage.Light': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Garage.Light"),
                'propagate': True
            },
            'Garage.NotificationManager': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Garage.NotificationManager"),
                'propagate': True
            },
            'Garage.Sensor': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Garage.Sensor"),
                'propagate': True
            },
            'Garage.mitzonURLCmdProcessor': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "Garage.mitzonURLCmdProcessor"),
                'propagate': True
            },
            'nanpy': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "nanpy"),
                'propagate': True
            },
            'nanpy.serialmanager': {
                'handlers': ['Garage'],
                'level': garageHandler.config_handler.getConfigParam("GARAGE_LOG_LEVEL", "nanpy.serialmanager"),
                'propagate': True
            },
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

    # Say starting and force a log rotation
    log=logging.getLogger('Garage.mitzonURLCmdProcessor')
    logh=logging._handlers.get('Garage')
    logh.doRollover()
    log.info("Starting Mitzon...")

    '''Subscriber - Dispatcher '''
    command_queue = Queue()
    response_queue = Queue()

    try:
        cherrypy.config.update(server_config)

        # dispatch_queue = Queue()
        # garageHandler = mitzonURLCmdProcessor(dispatch_queue)

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


        mitzon_valve_handler = ValveManager()
        thread_valve_manager = Thread(target=ValveManager.monitor,
                                       args=(mitzon_valve_handler,), name='valve_manager',
                                       daemon=True)
        
        notification_manager_handler = NotificationManager()
        thread_notification_manager = Thread(target=NotificationManager.processnotif,
                                       args=(notification_manager_handler,), name='notification_manager',
                                       daemon=True)

        thread_command_queue.start()
        thread_dispatcher.start()
        thread_garage_manager.start()
        thread_valve_manager.start()
        thread_notification_manager.start()

        cherrypy.quickstart(garageHandler, '/',garage_backend_conf)
    except Exception:
        log.error("Cherrypy quickstart fail !")
        traceback.print_exc()
        os._exit(-1)

    dispatch_queue.put(None)
    command_queue.put(None)

    # thread_command_queue.join(THREAD_TIMEOUTS)
    # thread_dispatcher.join(THREAD_TIMEOUTS)
    # thread_garage_manager.join(THREAD_TIMEOUTS)

    cherrypy.engine.exit()
    os._exit(0)

