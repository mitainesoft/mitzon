import cherrypy

try:
    from cheroot.wsgi import Server as WSGIServer
except ImportError:
    from cherrypy.wsgiserver import CherryPyWSGIServer as WSGIServer

class RootServer:
    @cherrypy.expose
    def index(self, **keywords):
        return "it works!"

if __name__ == '__main__':
    server_config={
        'server.socket_host': '0.0.0.0',
        'server.socket_port':8040,

        'server.ssl_module':'pyopenssl',
        'server.ssl_certificate':'/opt/mitainesoft/security/garageclient.pem',
        'server.ssl_private_key':'/opt/mitainesoft/security/garageclient.key.pem',
        # 'server.ssl_certificate_chain':'/home/ubuntu/gd_bundle.crt'
    }

    cherrypy.config.update(server_config)
    cherrypy.quickstart(RootServer())

