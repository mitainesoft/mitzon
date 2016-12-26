import cherrypy
from src.python.DeviceManager import DeviceManager


@cherrypy.expose
class DeviceControllerWebService():
    mything="THING1"
    myservice="SERV1"
    myid="ID1"   
    def __init__(self):
        self.mydevice = Device()
        print ("init DeviceControllerWebService stuff")
    @cherrypy.tools.accept(media='text/plain')    

	# s.post('http://127.0.0.1:8080/garage/open/g0')
    def _cp_dispatch(self, vpath):
        print ("JLC vpath=",vpath, "len=", len(vpath))
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
        print("JLC GET: no se!")
        return cherrypy.session['mything']

    @cherrypy.popargs('myservice')
    @cherrypy.popargs('myid')
    def POST(self, mything, myservice=None,myid=None):
        cherrypy.session['mything'] = mything
        cherrypy.session['myservice'] = myservice
        cherrypy.session['myid'] = myid
        print ("Garage Request Received POST: " , mything,myservice,myid)




        return some_string

    def PUT(self):
        cherrypy.session['myservice'] = self.myservice
        print ("JLC PUT: " , self.myservice,self.mything,self.myid )

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
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        }
    }
    cherrypy.config.update ({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 8080, 
                            })

    print("Rapberry Arduino connection Started...")
    cherrypy.quickstart(DeviceControllerWebService(), '/', conf)

    connecthandler=DeviceManager()
    
    