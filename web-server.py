#!/usr/bin/python3

import os, stat, atexit
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import time
import common

hostName = ""
hostPort = common.WEBSERVER_PORT
FIFO = common.FIFO
logger = common.homeSecurityLogger

serverWasStarted = False
@atexit.register
def exit_handler():
    logger.info("Exit command received. Should close web server")
    if serverWasStarted:
        myServer.server_close()
        logger.info("Web Server Stops - %s:%s" % (hostName, hostPort))
    else:
        logger.info("Web server was not started. Nothing to close")    

def writeToPipe(message):
    """
    check whether the named pipe exists and write to it
    Returns number of characters written or False otherwise
    """
    try:
        isFIFO = stat.S_ISFIFO(os.stat(FIFO).st_mode)
        if not isFIFO: raise FileNotFoundError
        logger.debug("Writing {} to IPC pipe".format(message))
        pipe = open(FIFO, 'w')
        count = pipe.write(message)
        logger.debug("Written {} chars to pipe".format(count))
        pipe.close()
        return count
    except FileNotFoundError:
        logger.critical("IPC write failed. File does not exist or is not a pipe")

    return False


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("Received\r\n", "utf-8"))
        query_components = parse_qs(urlparse(self.path).query)
        if('motion' in query_components):
            logger.info("Motion parameter set in request")
            writeToPipe(common.MOTION_DETECTED_COMMAND)

    def log_message(self, format, *args):
        logger.info("Request from {}:{} - ".format(self.client_address[0], self.client_address[1]) + format%args)


if __name__ == "__main__":
    try:
        myServer = HTTPServer((hostName, hostPort), MyServer)
    except Exception as e:
        logger.critical("Exception was raised while starting server: {}".format(str(e)))
        if not writeToPipe(common.WEBSERVER_FAIL_COMMAND):
            logger.critical("Can't signal fail state. Need to exit")
        exit(1)
    else:
        logger.info("Web Server Starts - %s:%s" % (hostName, hostPort))
        serverWasStarted = True
        if not writeToPipe(common.WEBSERVER_READY_COMMAND):
            logger.critical("Can't signal ready state. Need to exit")
            exit(1)
        try:
            myServer.serve_forever()
        except KeyboardInterrupt:
            pass

