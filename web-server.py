#!/usr/bin/python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import time

hostName = ""
hostPort = 9090

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("Received\r\n", "utf-8"))
        query_components = parse_qs(urlparse(self.path).query)
        print(query_components)


if __name__ == "__main__":
    myServer = HTTPServer((hostName, hostPort), MyServer)
    print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))
    try:
        myServer.serve_forever()
    except KeyboardInterrupt:
        pass
    
    myServer.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
