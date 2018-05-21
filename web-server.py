#!/usr/bin/python3

import os, stat
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import time
import common

hostName = ""
hostPort = 9090
FIFO = common.FIFO
logger = common.homeSecurityLogger

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("Received\r\n", "utf-8"))
        query_components = parse_qs(urlparse(self.path).query)
        #print(query_components)    
        #check whether the named pipe exists and write to it
        try:
            isFIFO = stat.S_ISFIFO(os.stat(FIFO).st_mode)
            if not isFIFO: raise FileNotFoundError
            logger.debug("Writing to IPC pipe")
            pipe = open(FIFO, 'w')
            count = pipe.write('TEST')
            logger.debug("Written {} chars to pipe".format(count))
            pipe.close()
        except FileNotFoundError:
            logger.critical("IPC write failed. File does not exist or is not a pipe")


if __name__ == "__main__":
    myServer = HTTPServer((hostName, hostPort), MyServer)
    logger.info("Web Server Starts - %s:%s" % (hostName, hostPort))
    try:
        myServer.serve_forever()
    except KeyboardInterrupt:
        pass

    myServer.server_close()
    logger.info("Web Server Stops - %s:%s" % (hostName, hostPort))
