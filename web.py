from http.server import BaseHTTPRequestHandler, HTTPServer
from web import get, post
import os

def getEnv(name,default=None):
    value = os.environ.get(name,None)
    if value == None:
        if default == None:
            value = input("Env variable not found, please enter {}: ".format(name))
        else:
            value = default
    return value

class S(BaseHTTPRequestHandler):
    def _set_headers(self,code,type):
        self.send_response(code)
        self.send_header('Content-type', type)
        self.end_headers()

    def do_GET(self):
        raw_data = self.rfile.read()
        data = get.handle(self.path,self.headers,raw_data)
        self._set_headers(data.code,data.type)
        self.wfile.write(data.response)

    def do_HEAD(self):
        self._set_headers(200, 'text/json')

    def do_POST(self):
        raw_data = self.rfile.read()
        data = post.handle(self.path,self.headers,raw_data)
        self._set_headers(data.code,data.type)
        self.wfile.write(data.response)

def run(server_class=HTTPServer, handler_class=S, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()

PORT = int(getEnv('PORT',5000))

run(port=PORT)
