#!/usr/bin/python3

try :
    import httplib
except:
    import http.client as httplib
import os
import subprocess
from time import sleep
import common

FIFO = common.FIFO
logger = common.homeSecurityLogger
serverMAC = common.NVR_SERVER_MAC_ADDRESS
serverIP = common.NVR_SERVER_IP_ADDRESS
serverPort = common.NVR_SERVER_PORT
nvrHost = "{}:{}".format(serverIP, serverPort)

def nvr_online():
    conn = httplib.HTTPConnection(nvrHost, timeout=5)
    try:
        conn.request("HEAD", "/")
        conn.close()
        return True
    except Exception as e:
        logger.error(str(e))
        conn.close()
        return False


if __name__ == "__main__":
    logger.info("Starting motioneye (NVR) server watchdog")
    logger.info("Server MAC Address: {}".format(serverMAC))
    logger.info("Server Host: {}".format(nvrHost))

    try:
        while True:
            logger.info("Pinging NVR server")
            nextSleepInterval = 600.
            if not nvr_online():
                logger.info("Ping failed, sending Wake-on-LAN")
                subprocess.call(["wakeonlan", serverMAC])
                nextSleepInterval = 30. #if server does not respond, check again sooner after sending WoL
            else:
                logger.info("Server is online")
            
            logger.debug("Will ping again after {} seconds".format(int(nextSleepInterval)))
            sleep(nextSleepInterval)
    except KeyboardInterrupt:
        pass
