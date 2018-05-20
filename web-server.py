#!/usr/bin/python3

import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import time
import common

hostName = ""
hostPort = 9090
FIFO = common.FIFO

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("Received\r\n", "utf-8"))
        query_components = parse_qs(urlparse(self.path).query)
        print(query_components)
        print("Writing to IPC pipe")
        pipe = open(FIFO, 'w')
        count = pipe.write('IPC CALL')
        print("Written {} chars".format(count))
        pipe.close()


if __name__ == "__main__":
    myServer = HTTPServer((hostName, hostPort), MyServer)
    print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))
    try:
        myServer.serve_forever()
    except KeyboardInterrupt:
        pass
    
    myServer.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
