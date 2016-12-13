import random
import string

import cherrypy
# import pydevd
# pydevd.settrace('192.168.1.83', port=8000, stdoutToServer=True, stderrToServer=True)

@cherrypy.expose
class DeviceControllerWebService():
    
    def __init__(self):
        self.device = Device()

	#s.post('http://127.0.0.1:8080/garage/open/g0')
    def _cp_dispatch(self, vpath):
        if len(vpath) == 1:
            cherrypy.request.params['myservice'] = vpath.pop() # ex: garage_door
            print ("myservice:", cherrypy.request.params['myservice']) 
            return self        
            
        if len(vpath) == 3:
            cherrypy.request.params['myservice'] = vpath.pop(0)  # ex: open close
            cherrypy.request.params['mydevice'] = vpath.pop(0) # /myid/
            cherrypy.request.params['myid'] = vpath.pop(0) # which one 0, 1, 2...
            return self.mydevice
            
        return vpath
        
    @cherrypy.tools.accept(media='text/plain')    
    def GET(self):
        return cherrypy.session['mystring']

    def POST(self, length=8):
        some_string = ''.join(random.sample(string.digits, int(length)))
        cherrypy.session['mystring'] = some_string
        return some_string

    def PUT(self, another_string):
        cherrypy.session['mystring'] = another_string

    def DELETE(self):
        cherrypy.session.pop('mystring', None)
    

class Device():
    @cherrypy.expose
    def index(self, mytask, myid):
        return 'About (%s) %s by %s...' % (myservice,mytask, myid)        

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
    cherrypy.quickstart(DeviceControllerWebService(), '/', conf)
    
    